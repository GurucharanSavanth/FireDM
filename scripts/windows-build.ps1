param(
    [string]$PythonExe,
    [string]$Channel = "dev",
    [ValidateSet("x64", "x86", "arm64")][string]$Arch = "x64",
    [switch]$SkipTests,
    [switch]$SkipLint,
    [switch]$SkipPythonPackage,
    [switch]$SkipTwineCheck,
    [switch]$SmokeGui,
    [switch]$Release,
    [switch]$PayloadOnly,
    [switch]$ValidateOnly,
    [switch]$Clean,
    [switch]$InstallLocalDeps,
    [string]$ReleaseDir = "release",
    [string]$BuildId,
    [string]$BuildDate,
    [switch]$AllowOverwrite,
    [switch]$IncludeRemoteTags,
    [switch]$IncludeGithubReleases,
    [switch]$PublishDraftRelease,
    [string]$GithubRepo,
    [string]$GithubTag
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot
$DistRoot = Join-Path $RepoRoot "dist"
$DistFireDM = Join-Path $DistRoot "FireDM"

if ($PublishDraftRelease) {
    $Release = $true
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

function Resolve-Python {
    param([string]$Requested)

    if ($Requested) {
        return (Resolve-Path $Requested).Path
    }

    $localVenv = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $localVenv) {
        return (Resolve-Path $localVenv).Path
    }

    $bootstrapVenv = Join-Path (Split-Path $RepoRoot -Parent) "FireDM-win-bootstrap\.venv\Scripts\python.exe"
    if (Test-Path $bootstrapVenv) {
        return (Resolve-Path $bootstrapVenv).Path
    }

    $discovered = & py -3.10 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.10 was not found. Pass -PythonExe explicitly."
    }

    return $discovered.Trim()
}

function Resolve-RepoChildPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $repoFullPath = [System.IO.Path]::GetFullPath($RepoRoot)
    $repoPrefix = $repoFullPath
    if (-not $repoPrefix.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $repoPrefix = $repoPrefix + [System.IO.Path]::DirectorySeparatorChar
    }

    if (-not $fullPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify path outside repository: $fullPath"
    }

    return $fullPath
}

function Remove-RepoDirectoryIfExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    $fullPath = Resolve-RepoChildPath -Path $Path
    if (Test-Path -LiteralPath $fullPath) {
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            try {
                Remove-Item -LiteralPath $fullPath -Recurse -Force
                return
            }
            catch {
                if ($attempt -eq 3) {
                    throw
                }
                Stop-PackagedProcesses
                Start-Sleep -Seconds 1
            }
        }
    }
}

function Remove-RepoFileIfExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    $fullPath = Resolve-RepoChildPath -Path $Path
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Force
    }
}

function New-CleanRepoDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    Remove-RepoDirectoryIfExists -Path $Path
    $fullPath = Resolve-RepoChildPath -Path $Path
    New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    return $fullPath
}

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $fullPath = Resolve-RepoChildPath -Path $Path
    $encoding = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($fullPath, $Content, $encoding)
}

function Get-FireDMVersion {
    $version = & $PythonExe -c "from firedm.version import __version__; print(__version__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read firedm.version.__version__"
    }

    return $version.Trim()
}

function Resolve-BuildId {
    param(
        [string]$RequestedBuildId,
        [string]$RequestedDate,
        [switch]$AllowExisting,
        [switch]$CheckRemoteTags,
        [switch]$CheckGithubReleases
    )

    $scriptPath = Join-Path $RepoRoot "scripts\release\build_id.py"
    $args = @($scriptPath, "--print-next", "--json")
    if ($RequestedBuildId) {
        $args += @("--build-id", $RequestedBuildId)
    }
    if ($RequestedDate) {
        $args += @("--date", $RequestedDate)
    }
    if ($AllowExisting) {
        $args += "--allow-overwrite"
    }
    if ($CheckRemoteTags) {
        $args += "--include-remote-tags"
    }
    if ($CheckGithubReleases) {
        $args += "--include-github-releases"
    }

    $json = & $PythonExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to resolve FireDM build ID."
    }

    return (($json -join "`n") | ConvertFrom-Json)
}

function Get-GitValue {
    param([string[]]$Arguments)

    try {
        $value = & git @Arguments
        if ($LASTEXITCODE -eq 0) {
            return ($value -join "`n").Trim()
        }
    }
    catch {
    }

    return ""
}

function Get-PackageArtifacts {
    if (-not (Test-Path -LiteralPath $DistRoot)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $DistRoot -File | Where-Object {
            $_.Name -like "*.whl" -or $_.Name -like "*.tar.gz"
        }
    )
}

function Get-PackagedProcesses {
    $distFullPath = [System.IO.Path]::GetFullPath($DistRoot)
    if (-not $distFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $distFullPath = $distFullPath + [System.IO.Path]::DirectorySeparatorChar
    }

    return @(
        Get-Process | Where-Object {
            try {
                $_.Path -and [System.IO.Path]::GetFullPath($_.Path).StartsWith(
                    $distFullPath,
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            }
            catch {
                $false
            }
        }
    )
}

function Stop-PackagedProcesses {
    $processes = Get-PackagedProcesses
    foreach ($process in $processes) {
        Write-Host "Stopping running packaged process:" $process.Id $process.ProcessName
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }

    if ($processes.Count -gt 0) {
        try {
            Wait-Process -Id ($processes | ForEach-Object { $_.Id }) -Timeout 5 -ErrorAction SilentlyContinue
        }
        catch {
        }
    }
}

function Invoke-ScopedLint {
    $lintTargets = @(
        "firedm\FireDM.py",
        "firedm\app_paths.py",
        "firedm\extractor_adapter.py",
        "firedm\ffmpeg_service.py",
        "firedm\tool_discovery.py",
        "firedm\setting.py",
        "firedm\update.py",
        "scripts\release",
        "tests"
    )

    Invoke-Checked $PythonExe (@("-m", "ruff", "check") + $lintTargets)
}

function Invoke-Compileall {
    Invoke-Checked $PythonExe @("-m", "compileall", ".\firedm", ".\scripts")
}

function Invoke-DependencyPreflight {
    param([switch]$SkipPortable)

    $args = @(
        "scripts\release\check_dependencies.py",
        "--arch",
        $Arch,
        "--channel",
        $Channel,
        "--build-id",
        $BuildId
    )
    if ($SkipPortable) {
        $args += "--skip-portable"
    }
    Invoke-Checked $PythonExe $args
}

function New-ReleasePackage {
    param(
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][string]$BuildId,
        [Parameter(Mandatory = $true)][object]$BuildInfo,
        [Parameter(Mandatory = $true)][string]$TestsStatus,
        [Parameter(Mandatory = $true)][string]$LintStatus,
        [Parameter(Mandatory = $true)][string]$PythonPackageStatus,
        [Parameter(Mandatory = $true)][string]$TwineStatus,
        [Parameter(Mandatory = $true)][string]$GuiSmokeStatus
    )

    if (-not (Test-Path -LiteralPath $DistFireDM)) {
        throw "Cannot create release package because dist\FireDM does not exist."
    }

    $releaseRoot = $ReleaseDir
    if (-not [System.IO.Path]::IsPathRooted($releaseRoot)) {
        $releaseRoot = Join-Path $RepoRoot $releaseRoot
    }
    $releaseRoot = Resolve-RepoChildPath -Path $releaseRoot
    New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

    $releaseName = "FireDM-$BuildId-windows-x64"
    $releaseOutput = New-CleanRepoDirectory -Path (Join-Path $releaseRoot $releaseName)
    $zipPath = Join-Path $releaseOutput "$releaseName.zip"
    $shaPath = Join-Path $releaseOutput "SHA256SUMS_$BuildId.txt"
    $manifestPath = Join-Path $releaseOutput "FireDM_release_manifest_$BuildId.json"
    $releaseBodyPath = Join-Path $releaseOutput "FireDM_release_notes_$BuildId.md"

    Remove-RepoFileIfExists -Path $zipPath
    Compress-Archive -Path (Join-Path $DistFireDM "*") -DestinationPath $zipPath -Force

    $packageCopies = @()
    foreach ($artifact in Get-PackageArtifacts) {
        $destination = Join-Path $releaseOutput $artifact.Name
        Copy-Item -LiteralPath $artifact.FullName -Destination $destination -Force
        $packageCopies += $destination
    }

    $commit = Get-GitValue -Arguments @("rev-parse", "HEAD")
    $status = Get-GitValue -Arguments @("status", "--short")
    $branch = Get-GitValue -Arguments @("branch", "--show-current")
    $createdUtc = (Get-Date).ToUniversalTime().ToString("o")

    $manifest = [ordered]@{
        name = $releaseName
        version = $Version
        build_id = $BuildId
        build_date = $BuildInfo.date
        build_index = $BuildInfo.index
        tag_name = $BuildInfo.tag
        release_name = $BuildInfo.release_name
        platform = "windows-x64"
        createdUtc = $createdUtc
        gitBranch = $branch
        gitCommit = $commit
        workingTreeDirty = -not [string]::IsNullOrWhiteSpace($status)
        python = (& $PythonExe -c "import sys; print(sys.version)")
        artifacts = @(
            [System.IO.Path]::GetFileName($zipPath)
        ) + ($packageCopies | ForEach-Object { [System.IO.Path]::GetFileName($_) }) + @(
            [System.IO.Path]::GetFileName($shaPath),
            [System.IO.Path]::GetFileName($manifestPath),
            [System.IO.Path]::GetFileName($releaseBodyPath)
        )
        validation = [ordered]@{
            pytest = $TestsStatus
            scopedRuff = $LintStatus
            pythonPackageBuild = $PythonPackageStatus
            twineCheck = $TwineStatus
            packagedHelpSmoke = "passed"
            packagedImportSmoke = "passed"
            guiSmoke = $GuiSmokeStatus
        }
    }
    $manifestJson = $manifest | ConvertTo-Json -Depth 5
    Write-Utf8File -Path $manifestPath -Content ($manifestJson + "`n")

    $bodyTemplate = @'
# FireDM {0}

Windows portable release generated by `scripts/windows-build.ps1 -Release`.

Build ID: `{1}`
Tag: `{2}`
Release name: `{3}`

## Assets

- `{4}.zip`: portable Windows one-folder build. Extract it, then run `FireDM-GUI.exe` for GUI mode or `firedm.exe --help` for CLI mode.
- Python wheel/sdist are included when the package build step is enabled.
- `SHA256SUMS_{1}.txt` contains SHA256 checksums for release assets.
- `FireDM_release_manifest_{1}.json` records build validation and git metadata.

## Validation performed by the build script

- pytest: {5}
- scoped Ruff: {6}
- Python package build: {7}
- Twine metadata check: {8}
- packaged CLI help smoke: passed
- packaged import smoke: passed
- GUI smoke: {9}

## Manual release checks still required

- Start the GUI and validate a normal direct-download flow.
- Validate one safe real video URL and one playlist URL.
- Validate one ffmpeg-required DASH/HLS item if this release claims media merge support.
- Keep ffmpeg and Deno external unless the release notes explicitly say they are bundled.
'@
    $body = $bodyTemplate -f $Version, $BuildId, $BuildInfo.tag, $BuildInfo.release_name, $releaseName, $TestsStatus, $LintStatus, $PythonPackageStatus, $TwineStatus, $GuiSmokeStatus
    Write-Utf8File -Path $releaseBodyPath -Content ($body + "`n")

    $hashFiles = @(
        Get-ChildItem -LiteralPath $releaseOutput -File | Where-Object {
            $_.Name -ne "SHA256SUMS.txt"
        } | Sort-Object Name
    )
    $hashLines = foreach ($file in $hashFiles) {
        $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
        "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), $file.Name
    }
    Write-Utf8File -Path $shaPath -Content (($hashLines -join "`n") + "`n")

    return [ordered]@{
        Name = $releaseName
        Output = $releaseOutput
        Zip = $zipPath
        Sha256 = $shaPath
        Manifest = $manifestPath
        Body = $releaseBodyPath
        PackageArtifacts = $packageCopies
        GitCommit = $commit
    }
}

function Write-PackagedBuildMetadata {
    param(
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][object]$BuildInfo
    )

    $commit = Get-GitValue -Arguments @("rev-parse", "HEAD")
    $status = Get-GitValue -Arguments @("status", "--short")
    $branch = Get-GitValue -Arguments @("branch", "--show-current")
    $createdUtc = (Get-Date).ToUniversalTime().ToString("o")
    $metadata = [ordered]@{
        version = $Version
        build_id = $BuildInfo.build_id
        build_date = $BuildInfo.date
        build_index = $BuildInfo.index
        tag_name = $BuildInfo.tag
        release_name = $BuildInfo.release_name
        platform = "windows-x64"
        createdUtc = $createdUtc
        gitBranch = $branch
        gitCommit = $commit
        workingTreeDirty = -not [string]::IsNullOrWhiteSpace($status)
        source = "scripts/windows-build.ps1"
    }
    $metadataPath = Join-Path $DistFireDM "build-metadata.json"
    Write-Utf8File -Path $metadataPath -Content (($metadata | ConvertTo-Json -Depth 5) + "`n")
}

function Publish-DraftGithubRelease {
    param(
        [Parameter(Mandatory = $true)]$ReleaseInfo,
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][object]$BuildInfo
    )

    $gh = Get-Command gh -ErrorAction Stop
    $tag = $GithubTag
    if (-not $tag) {
        $tag = $BuildInfo.tag
    }

    $assetArgs = @(
        "$($ReleaseInfo.Zip)#FireDM Windows portable zip",
        "$($ReleaseInfo.Sha256)#SHA256 checksums",
        "$($ReleaseInfo.Manifest)#Release manifest"
    )
    foreach ($artifact in $ReleaseInfo.PackageArtifacts) {
        $assetArgs += $artifact
    }

    $args = @("release", "create", $tag) + $assetArgs + @(
        "--draft",
        "--title", $BuildInfo.release_name,
        "--notes-file", $ReleaseInfo.Body
    )

    if ($ReleaseInfo.GitCommit) {
        $args += @("--target", $ReleaseInfo.GitCommit)
    }
    if ($GithubRepo) {
        $args += @("--repo", $GithubRepo)
    }

    Invoke-Checked $gh.Source $args
}

$PythonExe = Resolve-Python -Requested $PythonExe
Write-Host "Using Python:" $PythonExe

$Version = Get-FireDMVersion
Write-Host "Building FireDM version:" $Version

$BuildInfo = Resolve-BuildId `
    -RequestedBuildId $BuildId `
    -RequestedDate $BuildDate `
    -AllowExisting:$AllowOverwrite `
    -CheckRemoteTags:$IncludeRemoteTags `
    -CheckGithubReleases:$IncludeGithubReleases
$BuildId = $BuildInfo.build_id
Write-Host "Build ID:" $BuildId
Write-Host "Release tag:" $BuildInfo.tag

if ($Arch -ne "x64") {
    throw "$Arch build is blocked in this checkout; only x64 is implemented."
}

if ($PublishDraftRelease) {
    throw "scripts\windows-build.ps1 does not publish GitHub releases. Use scripts\release\github_release.py --publish after review."
}

if ($Clean) {
    Remove-RepoDirectoryIfExists -Path (Join-Path $RepoRoot "build")
    Remove-RepoDirectoryIfExists -Path $DistFireDM
}

if ($InstallLocalDeps) {
    Invoke-Checked $PythonExe @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    Invoke-Checked $PythonExe @("-m", "pip", "install", "--no-build-isolation", "-e", ".[dev,build]")
}

if (-not $PayloadOnly) {
    Invoke-DependencyPreflight -SkipPortable
    Invoke-Compileall
    if (-not $SkipTests) {
        Invoke-Checked $PythonExe @("-m", "pytest", "-q")
    }
    if (-not $SkipLint) {
        Invoke-ScopedLint
    }
    if ($ValidateOnly) {
        Write-Host "Validation-only dependency/build checks passed."
        return
    }

    $laneArgs = @(
        "scripts\release\build_windows.py",
        "--arch",
        $Arch,
        "--channel",
        $Channel,
        "--build-id",
        $BuildId,
        "--allow-overwrite"
    )
    Invoke-Checked $PythonExe $laneArgs
    Write-Host "Windows release lane completed."
    Write-Host "Artifacts are under dist\installers, dist\portable, dist\checksums, and dist\release-manifest.json."
    return
}

$testsStatus = "skipped"
$lintStatus = "skipped"
$pythonPackageStatus = "skipped"
$twineStatus = "skipped"
$guiSmokeStatus = "skipped"

if (-not $SkipTests) {
    Invoke-Checked $PythonExe @("-m", "pytest", "-q")
    $testsStatus = "passed"
}

if (-not $SkipLint) {
    Invoke-ScopedLint
    $lintStatus = "passed"
}

if (-not $SkipPythonPackage) {
    if (-not (Test-Path -LiteralPath $DistRoot)) {
        New-Item -ItemType Directory -Path $DistRoot -Force | Out-Null
    }
    Get-PackageArtifacts | ForEach-Object {
        Remove-RepoFileIfExists -Path $_.FullName
    }
    Invoke-Checked $PythonExe @("-m", "build", "--no-isolation")
    $pythonPackageStatus = "passed"
}

$packageArtifacts = Get-PackageArtifacts
if (-not $SkipTwineCheck) {
    if ($packageArtifacts.Count -eq 0) {
        throw "Twine check requested, but no wheel/sdist exists in dist. Re-run without -SkipPythonPackage."
    }
    Invoke-Checked $PythonExe (@("-m", "twine", "check") + ($packageArtifacts | ForEach-Object { $_.FullName }))
    $twineStatus = "passed"
}

Stop-PackagedProcesses
Remove-RepoDirectoryIfExists -Path (Join-Path $RepoRoot "build\pyinstaller")
Remove-RepoDirectoryIfExists -Path $DistFireDM

Invoke-Checked $PythonExe @(
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    "--distpath",
    $DistRoot,
    "--workpath",
    (Join-Path $RepoRoot "build\pyinstaller"),
    ".\scripts\firedm-win.spec"
)
Invoke-Checked ".\dist\FireDM\firedm.exe" @("--help")
Invoke-Checked ".\dist\FireDM\firedm.exe" @("--imports-only")

$RequiredTkAssets = @(
    ".\dist\FireDM\_internal\tkinter\__init__.py",
    ".\dist\FireDM\_internal\_tcl_data\init.tcl",
    ".\dist\FireDM\_internal\_tk_data\tk.tcl"
)

foreach ($Asset in $RequiredTkAssets) {
    if (-not (Test-Path $Asset)) {
        throw "Missing packaged Tk asset: $Asset. Keep the manual Tcl/Tk collection in scripts\firedm-win.spec."
    }
}

Write-PackagedBuildMetadata -Version $Version -BuildInfo $BuildInfo

if ($SmokeGui) {
    $process = Start-Process -FilePath ".\dist\FireDM\FireDM-GUI.exe" -PassThru
    Start-Sleep -Seconds 5
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id
    }
    $guiSmokeStatus = "passed"
}

$releaseInfo = $null
if ($Release) {
    $releaseInfo = New-ReleasePackage `
        -Version $Version `
        -BuildId $BuildId `
        -BuildInfo $BuildInfo `
        -TestsStatus $testsStatus `
        -LintStatus $lintStatus `
        -PythonPackageStatus $pythonPackageStatus `
        -TwineStatus $twineStatus `
        -GuiSmokeStatus $guiSmokeStatus

    Write-Host "Release package ready at" $releaseInfo.Output

    if ($PublishDraftRelease) {
        Publish-DraftGithubRelease -ReleaseInfo $releaseInfo -Version $Version -BuildInfo $BuildInfo
        Write-Host "Draft GitHub release created."
    }
}

Write-Host "Packaged build ready at .\dist\FireDM"
