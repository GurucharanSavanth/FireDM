[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Mode = "Release",

    [ValidateSet("OneFolder", "OneFile", "PortableZip")]
    [string]$Kind = "OneFolder",

    [ValidateSet("Auto", "PyInstaller", "Nuitka")]
    [string]$Backend = "Auto",

    [switch]$Clean,
    [switch]$NoClean,
    [switch]$DryRun,
    [switch]$SkipTests,
    [switch]$SkipSmoke,
    [string]$OutputDir = "release",
    [string]$Version = "",

    # Compatibility inputs accepted by the old scripts/windows-build.ps1 lane.
    [string]$PythonExe = "",
    [string]$Channel = "dev",
    [ValidateSet("x64", "x86", "arm64")]
    [string]$Arch = "x64",
    [string]$BuildId = "",
    [string]$BuildDate = "",
    [switch]$AllowOverwrite,
    [switch]$SkipLint,
    [switch]$SkipPythonPackage,
    [switch]$SkipTwineCheck,
    [switch]$PayloadOnly,
    [switch]$ValidateOnly,
    [switch]$InstallLocalDeps,
    [switch]$SmokeGui,
    [switch]$Release,
    [string]$ReleaseDir = "",
    [switch]$PublishDraftRelease,
    [string]$GithubRepo = "",
    [string]$GithubTag = ""
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$script:RepoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$script:ReleaseRoot = ""
$script:BuildLog = ""
$script:Warnings = New-Object System.Collections.Generic.List[object]
$script:BlockedItems = New-Object System.Collections.Generic.List[object]
$script:ValidationResults = New-Object System.Collections.Generic.List[object]
$script:CleanupActions = New-Object System.Collections.Generic.List[object]
$script:ChangelogSources = New-Object System.Collections.Generic.List[object]
$script:ReleaseArtifacts = New-Object System.Collections.Generic.List[object]
$script:Tools = @{}
$script:GitState = @{}
$script:PythonPath = ""
$script:BuildBackend = $Backend
$script:ResolvedVersion = ""
$script:ResolvedBuildId = ""
$script:EntryPoint = ""
$script:SpecFile = ""
$script:GuiBackend = "tkinter"
$script:GuiEntryPoint = "firedm.py"
$script:PluginManifest = $null

function Resolve-RepoPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$MustExist
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        $candidate = $Path
    } else {
        $candidate = Join-Path $script:RepoRoot $Path
    }

    $full = [System.IO.Path]::GetFullPath($candidate)
    if ($MustExist -and -not (Test-Path -LiteralPath $full)) {
        throw "Required path missing: $full"
    }
    return $full
}

function Test-UnderRepo {
    param([Parameter(Mandatory = $true)][string]$Path)

    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($script:RepoRoot).TrimEnd("\")
    if ([string]::Equals($full.TrimEnd("\"), $root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    $prefix = $root + "\"
    return $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $baseFull = [System.IO.Path]::GetFullPath($BasePath)
    if (-not $baseFull.EndsWith("\")) {
        $baseFull = $baseFull + "\"
    }
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    $baseUri = New-Object System.Uri($baseFull)
    $pathUri = New-Object System.Uri($pathFull)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace("/", "\")
}

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [string]$Level = "INFO"
    )

    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "[$stamp][$Level] $Message"
    Write-Host $line
    if ($script:BuildLog) {
        Add-Content -LiteralPath $script:BuildLog -Value $line -Encoding UTF8
    }
}

function Add-BuildWarning {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $script:Warnings.Add([pscustomobject]@{ code = $Code; message = $Message }) | Out-Null
    Write-Log $Message "WARN"
}

function Add-BlockedItem {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $script:BlockedItems.Add([pscustomobject]@{ code = $Code; message = $Message }) | Out-Null
    Write-Log $Message "BLOCKED"
}

function Add-ValidationResult {
    param(
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Command,
        [object]$ExitCode,
        [Parameter(Mandatory = $true)][string]$Result,
        [string]$Summary = ""
    )

    $script:ValidationResults.Add(
        [pscustomobject]@{
            stage = $Stage
            command = $Command
            exit_code = $ExitCode
            result = $Result
            summary = $Summary
        }
    ) | Out-Null
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )

    $display = $Command
    if ($Arguments.Count -gt 0) {
        $display = "$Command $($Arguments -join ' ')"
    }
    Write-Log "run: $display"

    if ($DryRun) {
        Add-ValidationResult -Stage $Stage -Command $display -ExitCode $null -Result "dry-run" -Summary "not executed"
        return
    }

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        # Native tools such as PyInstaller write normal progress to stderr.
        # Capture both streams and let the process exit code decide success.
        $ErrorActionPreference = "Continue"
        $output = & $Command @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    $summaryLines = New-Object System.Collections.Generic.List[string]
    foreach ($line in $output) {
        $text = $line.ToString()
        if ($summaryLines.Count -lt 20) {
            $summaryLines.Add($text) | Out-Null
        }
        Write-Log "  $text"
    }
    $result = "passed"
    if ($exitCode -ne 0) {
        $result = "failed"
    }
    Add-ValidationResult -Stage $Stage -Command $display -ExitCode $exitCode -Result $result -Summary ($summaryLines -join "`n")

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "Command failed with exit code ${exitCode}: $display"
    }
}

function Find-Tool {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    return ""
}

function Resolve-Python {
    if ($PythonExe) {
        $path = Resolve-RepoPath -Path $PythonExe
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "PythonExe was provided but not found: $path"
        }
        return $path
    }

    $venvPython = Join-Path (Join-Path $script:RepoRoot ".venv") "Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        return $venvPython
    }

    $tool = Find-Tool "python"
    if ($tool) {
        return $tool
    }
    throw "Python executable not found. Create .venv or pass -PythonExe."
}

function Get-GitValue {
    param([string[]]$Arguments)

    if (-not $script:Tools.git) {
        return ""
    }
    try {
        $output = & $script:Tools.git @Arguments 2>$null
    } catch {
        return ""
    }
    if ($LASTEXITCODE -ne 0) {
        return ""
    }
    return (($output | Out-String).Trim())
}

function Get-RepoState {
    if (-not $script:Tools.git) {
        return [pscustomobject]@{
            git_present = $false
            git_branch = ""
            git_commit = ""
            dirty_tree = $null
            status_short = "blocked: git not found"
        }
    }

    $inside = Get-GitValue -Arguments @("rev-parse", "--is-inside-work-tree")
    if ($inside -ne "true") {
        return [pscustomobject]@{
            git_present = $false
            git_branch = ""
            git_commit = ""
            dirty_tree = $null
            status_short = "blocked: not a git work tree"
        }
    }

    $status = Get-GitValue -Arguments @("status", "--short")
    return [pscustomobject]@{
        git_present = $true
        git_branch = Get-GitValue -Arguments @("branch", "--show-current")
        git_commit = Get-GitValue -Arguments @("rev-parse", "HEAD")
        dirty_tree = -not [string]::IsNullOrWhiteSpace($status)
        status_short = $status
    }
}

function Get-AppVersion {
    if ($Version) {
        return $Version
    }

    $versionFile = Join-Path (Join-Path $script:RepoRoot "firedm") "version.py"
    if (Test-Path -LiteralPath $versionFile -PathType Leaf) {
        $text = Get-Content -LiteralPath $versionFile -Raw
        $match = [regex]::Match($text, "__version__\s*=\s*['""]([^'""]+)['""]")
        if ($match.Success) {
            return $match.Groups[1].Value
        }
    }
    return "unknown"
}

function Get-DefaultBuildId {
    if ($BuildId) {
        return $BuildId
    }
    if ($BuildDate) {
        return "${BuildDate}_LOCAL"
    }
    return ((Get-Date).ToUniversalTime().ToString("yyyyMMdd") + "_LOCAL")
}

function Add-CleanupCandidate {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Plan,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Classification,
        [Parameter(Mandatory = $true)][string]$Reason,
        [string]$Action = "skip"
    )

    $full = Resolve-RepoPath -Path $Path
    $exists = Test-Path -LiteralPath $full
    $contained = Test-UnderRepo $full
    if (-not $contained) {
        $Classification = "forbidden"
        $Action = "skip"
        $Reason = "path is outside repo root"
    }
    $Plan.Add(
        [pscustomobject]@{
            path = $full
            relative_path = if ($contained) { Get-RelativePath -BasePath $script:RepoRoot -Path $full } else { $full }
            classification = $Classification
            action = $Action
            exists = $exists
            reason = $Reason
        }
    ) | Out-Null
}

function Get-CleanupPlan {
    $plan = New-Object System.Collections.Generic.List[object]

    Add-CleanupCandidate $plan "firedm\_build_info.py" "safe" "auto-generated build info stamp; regenerated each build" "remove-if-clean"
    Add-CleanupCandidate $plan "build" "safe" "generated build work tree" "remove-if-clean"
    Add-CleanupCandidate $plan "dist" "safe" "generated legacy release/build output; root release is canonical after this patch" "remove-if-clean"
    Add-CleanupCandidate $plan ".pytest_cache" "safe" "pytest cache" "remove-if-clean"
    Add-CleanupCandidate $plan ".mypy_cache" "safe" "mypy cache" "remove-if-clean"
    Add-CleanupCandidate $plan ".ruff_cache" "safe" "ruff cache" "remove-if-clean"
    Add-CleanupCandidate $plan "FireDM.egg-info" "safe" "generated setuptools metadata" "remove-if-clean"
    Add-CleanupCandidate $plan ".coverage" "safe" "coverage data file" "remove-if-clean"
    Add-CleanupCandidate $plan "htmlcov" "safe" "coverage HTML output" "remove-if-clean"
    Add-CleanupCandidate $plan "build\windows-build" "safe" "canonical Windows build staging folder" "remove-if-clean"
    Add-CleanupCandidate $plan "release\staging" "safe" "legacy canonical release staging folder" "remove-if-clean"
    Add-CleanupCandidate $plan "release\work" "safe" "legacy canonical release work folder" "remove-if-clean"
    Add-CleanupCandidate $plan "release\temp" "safe" "legacy canonical release temporary folder" "remove-if-clean"
    Add-CleanupCandidate $plan "release\FireDM" "safe" "canonical one-folder app output" "remove-if-clean"
    Add-CleanupCandidate $plan "release\FireDM.zip" "safe" "canonical portable zip output" "remove-if-clean"

    if (Test-Path -LiteralPath $script:ReleaseRoot -PathType Container) {
        Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "\.whl$|\.tar\.gz$" } |
            ForEach-Object {
                Add-CleanupCandidate $plan $_.FullName "safe" "generated Python distribution artifact under root release" "remove-if-clean"
            }

        Get-ChildItem -LiteralPath $script:ReleaseRoot -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "^FireDM-.+-windows-(x64|x86|arm64)(\.(zip|exe|msi))?$" } |
            ForEach-Object {
                Add-CleanupCandidate $plan $_.FullName "safe" "explicitly matched generated Windows release artifact under root release" "remove-if-clean"
            }
    }

    foreach ($rootName in @("firedm", "scripts", "tests")) {
        $root = Join-Path $script:RepoRoot $rootName
        if (Test-Path -LiteralPath $root) {
            Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue |
                ForEach-Object { Add-CleanupCandidate $plan $_.FullName "safe" "generated Python bytecode cache" "remove-if-clean" }
            Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction SilentlyContinue |
                Where-Object { $_.Extension -in @(".pyc", ".pyo") } |
                ForEach-Object { Add-CleanupCandidate $plan $_.FullName "safe" "generated Python bytecode file" "remove-if-clean" }
        }
    }

    Add-CleanupCandidate $plan ".git" "forbidden" "git history and working tree metadata must not be removed" "skip"
    Add-CleanupCandidate $plan ".venv" "forbidden" "repo-local toolchain must not be removed by build cleanup" "skip"
    Add-CleanupCandidate $plan "docs" "forbidden" "source documentation" "skip"
    Add-CleanupCandidate $plan "scripts" "forbidden" "source build scripts" "skip"
    Add-CleanupCandidate $plan "tests" "forbidden" "source tests" "skip"
    Add-CleanupCandidate $plan "firedm" "forbidden" "application source" "skip"
    Add-CleanupCandidate $plan "artifacts" "forbidden" "mixed tracked evidence and generated reports; requires separate review" "skip"
    Add-CleanupCandidate $plan "browser_extension" "unknown" "source-like browser extension files are not proven generated" "skip"
    Add-CleanupCandidate $plan "package-lock.json" "unknown" "dependency metadata not proven disposable in this checkout" "skip"

    return $plan
}

function Invoke-CleanupPlan {
    param([Parameter(Mandatory = $true)][System.Collections.Generic.List[object]]$Plan)

    if ($NoClean) {
        foreach ($item in $Plan) {
            $script:CleanupActions.Add([pscustomobject]@{
                path = $item.relative_path
                classification = $item.classification
                action = "skipped"
                reason = "NoClean selected"
            }) | Out-Null
        }
        Write-Log "cleanup skipped by -NoClean"
        return
    }

    foreach ($item in $Plan) {
        $action = "skipped"
        $reason = $item.reason
        if ($Clean -and $item.exists -and $item.classification -eq "safe") {
            if ($DryRun) {
                $action = "would_remove"
            } else {
                if (-not (Test-UnderRepo $item.path)) {
                    throw "Cleanup target escaped repo root: $($item.path)"
                }
                if (-not (Test-Path -LiteralPath $item.path)) {
                    $action = "skipped"
                    $reason = "$reason; target already removed by earlier cleanup action"
                } elseif ($PSCmdlet.ShouldProcess($item.path, "Remove generated build artifact")) {
                    Remove-Item -LiteralPath $item.path -Recurse -Force
                    $action = "removed"
                } else {
                    $action = "whatif_skipped"
                }
            }
        } elseif ($Clean -and $item.exists -and $item.classification -ne "safe") {
            $action = "blocked"
        }

        $script:CleanupActions.Add([pscustomobject]@{
            path = $item.relative_path
            classification = $item.classification
            action = $action
            reason = $reason
        }) | Out-Null
        Write-Log "cleanup $action [$($item.classification)] $($item.relative_path): $reason"
    }
}

function Invoke-BuildInfoStamp {
    Write-Log "Stage 4 build info stamp"
    $buildInfoPath = Join-Path (Join-Path $script:RepoRoot "firedm") "_build_info.py"

    # Build each line explicitly - avoids heredoc edge cases in PS 5.1.
    $gitDirtyStr = "False"
    if ($script:GitState.dirty_tree) { $gitDirtyStr = "True" }

    $lines = @(
        "# Auto-generated by windows-build.ps1 - do not edit or commit.",
        "APP_VERSION = `"$($script:ResolvedVersion)`"",
        "BUILD_ID = `"$($script:ResolvedBuildId)`"",
        "BUILD_MODE = `"$Mode`"",
        "BUILD_BACKEND = `"$($script:BuildBackend)`"",
        "GUI_BACKEND = `"$($script:GuiBackend)`"",
        "GIT_BRANCH = `"$($script:GitState.git_branch)`"",
        "GIT_COMMIT = `"$($script:GitState.git_commit)`"",
        "GIT_DIRTY = $gitDirtyStr"
    )

    if (-not $DryRun) {
        Set-Content -LiteralPath $buildInfoPath -Value ($lines -join "`n") -Encoding UTF8
        Write-Log "wrote: $buildInfoPath"
    } else {
        Write-Log "dry-run: would write $buildInfoPath"
    }
    Add-ValidationResult -Stage "build-info" -Command "Write _build_info.py" -ExitCode 0 -Result "passed" `
        -Summary "version=$($script:ResolvedVersion) build_id=$($script:ResolvedBuildId)"
}

function Test-ArtifactIntegrity {
    Write-Log "Stage 8 artifact integrity"
    if ($DryRun) {
        Add-ValidationResult -Stage "artifact-check" -Command "artifact integrity" -ExitCode $null -Result "dry-run" -Summary "not executed"
        return
    }
    $appDir = Join-Path $script:ReleaseRoot "FireDM"
    if (-not (Test-Path -LiteralPath $appDir -PathType Container)) {
        throw "Release app folder missing: $appDir"
    }

    $failures = [System.Collections.ArrayList]@()
    $ok       = [System.Collections.ArrayList]@()

    foreach ($exeName in @("firedm.exe", "FireDM-GUI.exe")) {
        $exePath = Join-Path $appDir $exeName
        if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
            [void]$failures.Add("MISSING required: $exeName")
        } else {
            $szMB = [int]((Get-Item -LiteralPath $exePath).Length / 1MB)
            if ($szMB -lt 1) {
                [void]$failures.Add("TOO SMALL: $exeName ($szMB MB)")
            } else {
                [void]$ok.Add("$exeName ($szMB MB)")
            }
        }
    }

    foreach ($item in $ok)       { Write-Log "artifact ok: $item" }
    foreach ($item in $failures)  { Write-Log "artifact FAIL: $item" "ERROR" }

    $allItems = @($ok) + @($failures)
    $summary  = $allItems -join "; "
    $exitCode = 0
    $result   = "passed"
    if ($failures.Count -gt 0) {
        $exitCode = 1
        $result   = "failed"
    }
    Add-ValidationResult -Stage "artifact-check" -Command "artifact integrity" -ExitCode $exitCode -Result $result -Summary $summary

    if ($failures.Count -gt 0) {
        $msg = "Artifact integrity check failed: " + ($failures -join ", ")
        throw $msg
    }
}

function Write-BuildSummary {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  FireDM Build Summary" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Version   : $($script:ResolvedVersion)"
    Write-Host "  Build ID  : $($script:ResolvedBuildId)"
    Write-Host "  Backend   : $($script:BuildBackend)"
    Write-Host "  GUI       : $($script:GuiBackend)"
    Write-Host "  Mode      : $Mode"
    Write-Host "  Output    : $script:ReleaseRoot"
    Write-Host ""

    $pass = 0
    $fail = 0
    $skip = 0
    foreach ($r in $script:ValidationResults) {
        $tag = $r.result.ToUpper().PadRight(8)
        $color = "White"
        if ($r.result -eq "passed")  { $color = "Green";  $pass++ }
        elseif ($r.result -eq "failed")  { $color = "Red";    $fail++ }
        else                             { $color = "Yellow"; $skip++ }
        Write-Host "  [$tag] $($r.stage) - $($r.command)" -ForegroundColor $color
    }

    if ($script:Warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "  Warnings ($($script:Warnings.Count)):" -ForegroundColor Yellow
        foreach ($w in $script:Warnings) {
            Write-Host "    [WARN] $($w.code): $($w.message)" -ForegroundColor Yellow
        }
    }
    if ($script:BlockedItems.Count -gt 0) {
        Write-Host ""
        Write-Host "  Blocked ($($script:BlockedItems.Count)):" -ForegroundColor DarkYellow
        foreach ($b in $script:BlockedItems) {
            Write-Host "    [BLOCKED] $($b.code): $($b.message)" -ForegroundColor DarkYellow
        }
    }

    Write-Host ""
    $overallColor  = "Green"
    $overallStatus = "PASSED"
    if ($fail -gt 0) {
        $overallColor  = "Red"
        $overallStatus = "FAILED"
    }
    Write-Host "  Result: $overallStatus  (pass=$pass fail=$fail skip=$skip)" -ForegroundColor $overallColor
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-PythonModule {
    param([Parameter(Mandatory = $true)][string]$ModuleName)

    if ($DryRun) {
        return $true
    }
    & $script:PythonPath -c "import $ModuleName" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-DependencyChecks {
    Write-Log "Stage 3 dependency/runtime checks"

    if (-not (Test-Path -LiteralPath (Join-Path $script:RepoRoot "pyproject.toml") -PathType Leaf)) {
        throw "pyproject.toml missing"
    }
    $script:EntryPoint = Join-Path $script:RepoRoot "firedm.py"
    if (-not (Test-Path -LiteralPath $script:EntryPoint -PathType Leaf)) {
        throw "entry point missing: $($script:EntryPoint)"
    }
    $script:SpecFile = Join-Path (Join-Path $script:RepoRoot "scripts") "firedm-win.spec"
    if ($script:BuildBackend -eq "Auto") {
        $script:BuildBackend = "PyInstaller"
    }

    if ($script:BuildBackend -eq "PyInstaller" -and -not $DryRun -and -not (Test-PythonModule "PyInstaller")) {
        throw "PyInstaller is required for Backend=PyInstaller. Install it in the repo venv."
    }
    if ($script:BuildBackend -eq "PyInstaller" -and -not (Test-Path -LiteralPath $script:SpecFile -PathType Leaf)) {
        throw "PyInstaller spec missing: $($script:SpecFile)"
    }
    if ($script:BuildBackend -eq "Nuitka") {
        $nuitka = Find-Tool "nuitka"
        if (-not $nuitka) {
            throw "Nuitka backend selected but nuitka is not available on PATH."
        }
    }
    if ($Arch -ne "x64") {
        throw "Windows $Arch build is blocked in this checkout; only x64 is currently validated."
    }
    if ($InstallLocalDeps) {
        throw "-InstallLocalDeps is blocked in the canonical script; prepare the repo venv explicitly."
    }
    if ($PublishDraftRelease -or $GithubRepo -or $GithubTag) {
        throw "windows-build.ps1 does not publish GitHub releases. Use scripts/release/github_release.py after artifact review."
    }
    if ($ReleaseDir) {
        Add-BuildWarning "legacy-release-dir" "-ReleaseDir is accepted for compatibility but root .\release remains canonical."
    }
    if ($SmokeGui) {
        Add-BuildWarning "gui-smoke-not-default" "-SmokeGui is accepted for compatibility; this script does not launch the full GUI by default."
    }
}

function Invoke-QA {
    Write-Log "Stage 4 QA"
    if ($Mode -eq "Release" -and -not $SkipTests) {
        Add-ValidationResult -Stage "qa" -Command "all QA checks" -ExitCode $null -Result "skipped" -Summary "Release mode; use -Mode Debug for full QA suite"
        return
    }
    if ($SkipTests) {
        Add-ValidationResult -Stage "qa" -Command "all QA checks" -ExitCode $null -Result "skipped" -Summary "SkipTests selected"
        return
    }

    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @(
        "-m", "compileall", "-q",
        ".\firedm",
        ".\scripts\release"
    )
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_frontend_common_view_models.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_frontend_common_adapters.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_plugin_manifest.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_download_engines.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_internal_http_engine.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q", "tests\test_engine_config_and_factory.py")
    Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "pytest", "-q")

    if (Test-PythonModule "mypy") {
        Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @("-m", "mypy")
    } else {
        Add-BuildWarning "mypy-unavailable" "mypy is unavailable in the selected Python environment; type check skipped."
        Add-ValidationResult -Stage "qa" -Command "$($script:PythonPath) -m mypy" -ExitCode $null -Result "skipped" -Summary "module unavailable"
    }

    if (-not $SkipLint) {
        if (Test-PythonModule "ruff") {
            Invoke-CheckedCommand -Stage "qa" -Command $script:PythonPath -Arguments @(
                "-m", "ruff", "check",
                ".\firedm\download_engines",
                ".\firedm\frontend_common",
                ".\firedm\plugins\manifest.py",
                ".\firedm\plugins\policy.py",
                ".\firedm\plugins\registry.py",
                ".\tests\test_download_engines.py",
                ".\tests\test_internal_http_engine.py",
                ".\tests\test_engine_config_and_factory.py",
                ".\tests\test_frontend_common_view_models.py",
                ".\tests\test_frontend_common_adapters.py",
                ".\tests\test_plugin_manifest.py",
                ".\tests\test_plugins.py",
                ".\tests\test_user_sovereignty.py"
            )
        } else {
            Add-BuildWarning "ruff-unavailable" "ruff is unavailable in the selected Python environment; scoped lint skipped."
            Add-ValidationResult -Stage "qa" -Command "$($script:PythonPath) -m ruff check <scoped>" -ExitCode $null -Result "skipped" -Summary "module unavailable"
        }
    } else {
        Add-ValidationResult -Stage "qa" -Command "scoped ruff" -ExitCode $null -Result "skipped" -Summary "SkipLint selected"
    }
}

function Invoke-PythonDistributionBuild {
    Write-Log "Stage 5b Python distribution build"
    if ($SkipPythonPackage) {
        Add-ValidationResult -Stage "python-package" -Command "python -m build --sdist --wheel" -ExitCode $null -Result "skipped" -Summary "SkipPythonPackage selected"
        return
    }
    if ($ValidateOnly) {
        Add-ValidationResult -Stage "python-package" -Command "python -m build --sdist --wheel" -ExitCode $null -Result "skipped" -Summary "ValidateOnly selected"
        return
    }
    if ($DryRun) {
        Add-ValidationResult -Stage "python-package" -Command "python -m build --sdist --wheel --no-isolation --outdir release" -ExitCode $null -Result "dry-run" -Summary "not executed"
        Add-BlockedItem "python-package-dry-run" "DryRun did not produce wheel or source distribution artifacts."
        return
    }
    if (-not (Test-PythonModule "build")) {
        throw "Python package build requires the 'build' module. Install the repo build extras or pass -SkipPythonPackage."
    }

    foreach ($oldPackage in Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "\.whl$|\.tar\.gz$" }) {
        if (-not (Test-UnderRepo $oldPackage.FullName)) {
            throw "Python package cleanup target escaped repo root: $($oldPackage.FullName)"
        }
        Remove-Item -LiteralPath $oldPackage.FullName -Force
    }

    Invoke-CheckedCommand -Stage "python-package" -Command $script:PythonPath -Arguments @(
        "-m", "build",
        "--sdist",
        "--wheel",
        "--no-isolation",
        "--outdir", $script:ReleaseRoot
    )

    $wheelFiles = @(Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Force -Filter "*.whl" -ErrorAction SilentlyContinue)
    $sdistFiles = @(Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Force -Filter "*.tar.gz" -ErrorAction SilentlyContinue)
    if ($wheelFiles.Count -ne 1 -or $sdistFiles.Count -ne 1) {
        throw "Expected exactly one .whl and one .tar.gz in release output; found $($wheelFiles.Count) wheel(s), $($sdistFiles.Count) sdist(s)."
    }

    foreach ($file in @($wheelFiles + $sdistFiles)) {
        $relative = (Get-RelativePath -BasePath $script:ReleaseRoot -Path $file.FullName).Replace("\", "/")
        $kind = "pythonSdist"
        if ($file.Extension -eq ".whl") {
            $kind = "pythonWheel"
        }
        $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = $kind; path = $relative }) | Out-Null
        Write-Log "python package artifact: $relative"
    }

    if ($SkipTwineCheck) {
        Add-ValidationResult -Stage "python-package" -Command "twine check release\\*.whl release\\*.tar.gz" -ExitCode $null -Result "skipped" -Summary "SkipTwineCheck selected"
    } elseif (Test-PythonModule "twine") {
        $twineArgs = @("-m", "twine", "check")
        foreach ($file in @($wheelFiles + $sdistFiles)) {
            $twineArgs += $file.FullName
        }
        Invoke-CheckedCommand -Stage "python-package" -Command $script:PythonPath -Arguments $twineArgs
    } else {
        Add-BuildWarning "twine-unavailable" "twine is unavailable in the selected Python environment; Python distribution metadata check skipped."
        Add-ValidationResult -Stage "python-package" -Command "$($script:PythonPath) -m twine check release\*.whl release\*.tar.gz" -ExitCode $null -Result "skipped" -Summary "module unavailable"
    }
}

function Invoke-PackageBuild {
    Write-Log "Stage 5 package build"
    if ($ValidateOnly) {
        Add-ValidationResult -Stage "package" -Command "package build" -ExitCode $null -Result "skipped" -Summary "ValidateOnly selected"
        return
    }
    if ($script:BuildBackend -eq "Nuitka") {
        if ($DryRun) {
            Add-ValidationResult -Stage "package" -Command "nuitka <args>" -ExitCode $null -Result "dry-run" -Summary "not executed"
            return
        }
        throw "Nuitka build is blocked until compiler discovery and standalone data handling are validated."
    }
    if ($Kind -eq "OneFile") {
        if ($DryRun) {
            Add-ValidationResult -Stage "package" -Command "PyInstaller one-file" -ExitCode $null -Result "dry-run" -Summary "one-file would require a validated one-file spec"
            Add-BlockedItem "onefile-unvalidated" "PyInstaller one-file is parameter-supported but blocked for real builds until a one-file spec is validated."
            return
        }
        throw "PyInstaller one-file is blocked until a one-file spec is validated."
    }

    $stageRoot = Join-Path (Join-Path $script:RepoRoot "build") "windows-build\staging"
    $distPath = Join-Path $stageRoot "pyinstaller-dist"
    $workPath = Join-Path $stageRoot "pyinstaller-work"
    if ($PayloadOnly) {
        $distPath = Join-Path $script:RepoRoot "dist"
        $workPath = Join-Path (Join-Path $script:RepoRoot "build") "pyinstaller"
    }
    $args = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath", $distPath,
        "--workpath", $workPath,
        $script:SpecFile
    )

    Invoke-CheckedCommand -Stage "package" -Command $script:PythonPath -Arguments $args

    if ($DryRun) {
        Add-BlockedItem "package-dry-run" "DryRun did not produce app artifacts."
        return
    }

    $source = Join-Path $distPath "FireDM"
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "PyInstaller did not produce expected folder: $source"
    }

    $releaseApp = Join-Path $script:ReleaseRoot "FireDM"
    if (Test-Path -LiteralPath $releaseApp) {
        Remove-Item -LiteralPath $releaseApp -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $releaseApp -Recurse
    $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = "appFolder"; path = "FireDM" }) | Out-Null

    $legacyDist = Join-Path $script:RepoRoot "dist"
    $legacyApp = Join-Path $legacyDist "FireDM"
    if (-not [string]::Equals([System.IO.Path]::GetFullPath($source), [System.IO.Path]::GetFullPath($legacyApp), [System.StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path -LiteralPath $legacyApp) {
            Remove-Item -LiteralPath $legacyApp -Recurse -Force
        }
        New-Item -ItemType Directory -Path $legacyDist -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $legacyApp -Recurse
        Add-BuildWarning "legacy-dist-mirror" "Copied one-folder payload to dist\FireDM only for existing release-script compatibility; root .\release remains canonical."
    }

    if ($Kind -eq "PortableZip") {
        $zip = Join-Path $script:ReleaseRoot "FireDM.zip"
        if (Test-Path -LiteralPath $zip) {
            Remove-Item -LiteralPath $zip -Force
        }
        Compress-Archive -Path (Join-Path $releaseApp "*") -DestinationPath $zip
        $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = "portableZip"; path = "FireDM.zip" }) | Out-Null
    }
}

function Get-PluginManifestSection {
    Write-Log "Stage 7a plugin manifest discovery"
    if ($DryRun) {
        $script:PluginManifest = [ordered]@{
            included = @()
            blocked = @()
            planned = @()
            discovery_warnings = @("dry-run did not invoke Python")
        }
        Add-ValidationResult -Stage "plugin-manifest" -Command "discover_plugin_manifest" -ExitCode $null -Result "dry-run" -Summary "skipped under DryRun"
        return
    }
    $cmd = "import contextlib, io, json, sys; buf = io.StringIO(); orig = sys.stdout; sys.stdout = buf; from firedm.plugins.manifest import discover_plugin_manifest; section = discover_plugin_manifest(); sys.stdout = orig; sys.stdout.write('PLUGIN_MANIFEST_JSON_BEGIN'); sys.stdout.write(json.dumps(section.to_serializable())); sys.stdout.write('PLUGIN_MANIFEST_JSON_END')"
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $script:PythonPath -c $cmd 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($exitCode -ne 0) {
        Add-BuildWarning "plugin-manifest-failed" "Plugin manifest discovery failed (exit ${exitCode}); release manifest plugin section will be empty."
        $script:PluginManifest = [ordered]@{
            included = @()
            blocked = @()
            planned = @()
            discovery_warnings = @("python invocation failed: exit ${exitCode}")
        }
        return
    }
    $allText = ($output | Out-String)
    $beginMarker = "PLUGIN_MANIFEST_JSON_BEGIN"
    $endMarker = "PLUGIN_MANIFEST_JSON_END"
    $beginIdx = $allText.IndexOf($beginMarker)
    $endIdx = $allText.IndexOf($endMarker)
    $jsonText = ""
    if ($beginIdx -ge 0 -and $endIdx -gt $beginIdx) {
        $startOffset = $beginIdx + $beginMarker.Length
        $jsonText = $allText.Substring($startOffset, $endIdx - $startOffset).Trim()
    }
    try {
        if (-not $jsonText) { throw "no JSON payload found between markers" }
        $script:PluginManifest = $jsonText | ConvertFrom-Json
    } catch {
        Add-BuildWarning "plugin-manifest-parse-failed" "Plugin manifest JSON could not be parsed; release manifest plugin section will be empty."
        $script:PluginManifest = [ordered]@{
            included = @()
            blocked = @()
            planned = @()
            discovery_warnings = @("JSON parse failed")
        }
    }
    Add-ValidationResult -Stage "plugin-manifest" -Command "discover_plugin_manifest" -ExitCode $exitCode -Result "passed" -Summary "discovered plugin manifest"
}

function Get-ObjectPropertyValue {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) {
        return @()
    }
    if ($Object -is [System.Collections.IDictionary]) {
        return $Object[$Name]
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($property) {
        return $property.Value
    }
    return @()
}

function Add-PluginSummaryLines {
    param(
        [Parameter(Mandatory = $true)][object]$LineList,
        [Parameter(Mandatory = $true)][string]$Label,
        [AllowNull()][object]$Entries
    )

    foreach ($entry in @($Entries)) {
        if ($null -eq $entry) {
            continue
        }
        $pluginId = Get-ObjectPropertyValue -Object $entry -Name "plugin_id"
        $version = Get-ObjectPropertyValue -Object $entry -Name "version"
        $status = Get-ObjectPropertyValue -Object $entry -Name "status"
        $reason = Get-ObjectPropertyValue -Object $entry -Name "blocked_reason"
        $overridable = Get-ObjectPropertyValue -Object $entry -Name "user_overridable"
        $line = "$Label $pluginId v$version [$status]"
        if ($reason) {
            $overridableTag = if ($overridable) { "user-overridable" } else { "permanent" }
            $line = "$line block=$overridableTag reason=$reason"
        }
        $LineList.Add($line) | Out-Null
    }
}

function Write-PluginManifestArtifacts {
    Write-Log "Stage 7b plugin manifest artifacts"
    if (-not $script:PluginManifest) {
        $script:PluginManifest = [ordered]@{
            included = @()
            blocked = @()
            planned = @()
            discovery_warnings = @("plugin manifest discovery did not run")
        }
    }

    $jsonPath = Join-Path $script:ReleaseRoot "plugins-manifest.json"
    $textPath = Join-Path $script:ReleaseRoot "plugins-manifest.txt"
    $script:PluginManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $pluginLines = New-Object System.Collections.ArrayList
    $pluginLines.Add("FireDM Plugin Manifest") | Out-Null
    $pluginLines.Add("build_id=$($script:ResolvedBuildId)") | Out-Null
    $pluginLines.Add("status=discovered-not-enabled") | Out-Null
    $pluginLines.Add("") | Out-Null

    Add-PluginSummaryLines -LineList $pluginLines -Label "included" -Entries (Get-ObjectPropertyValue -Object $script:PluginManifest -Name "included")
    Add-PluginSummaryLines -LineList $pluginLines -Label "blocked" -Entries (Get-ObjectPropertyValue -Object $script:PluginManifest -Name "blocked")
    Add-PluginSummaryLines -LineList $pluginLines -Label "planned" -Entries (Get-ObjectPropertyValue -Object $script:PluginManifest -Name "planned")
    foreach ($warning in @(Get-ObjectPropertyValue -Object $script:PluginManifest -Name "discovery_warnings")) {
        if ($warning) {
            $pluginLines.Add("warning $warning") | Out-Null
        }
    }
    if ($pluginLines.Count -eq 4) {
        $pluginLines.Add("no plugins discovered") | Out-Null
    }

    Set-Content -LiteralPath $textPath -Value ($pluginLines -join "`n") -Encoding UTF8
    $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = "pluginManifestJson"; path = "plugins-manifest.json" }) | Out-Null
    $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = "pluginManifestText"; path = "plugins-manifest.txt" }) | Out-Null

    # Copy optional dependency list for advanced features (user-sovereignty)
    $advReqSrc = Join-Path $PSScriptRoot "requirements-advanced.txt"
    if (Test-Path -LiteralPath $advReqSrc -PathType Leaf) {
        $advReqDest = Join-Path $script:ReleaseRoot "requirements-advanced.txt"
        Copy-Item -LiteralPath $advReqSrc -Destination $advReqDest -Force
        $script:ReleaseArtifacts.Add([pscustomobject]@{ kind = "advancedRequirements"; path = "requirements-advanced.txt" }) | Out-Null
    }

    Add-ValidationResult -Stage "plugin-artifacts" -Command "write plugin manifest artifacts" -ExitCode 0 -Result "passed" -Summary "plugins-manifest.json; plugins-manifest.txt; requirements-advanced.txt"
}

function Invoke-SmokeCheck {
    Write-Log "Stage 10 smoke check"
    if ($SkipSmoke) {
        Add-ValidationResult -Stage "smoke" -Command "release smoke" -ExitCode $null -Result "skipped" -Summary "SkipSmoke selected"
        return
    }
    if ($DryRun) {
        Add-ValidationResult -Stage "smoke" -Command "release smoke" -ExitCode $null -Result "dry-run" -Summary "not executed"
        Add-BlockedItem "gui-smoke-dry-run" "DryRun did not launch packaged CLI or GUI smoke checks."
        return
    }

    $exe = Join-Path (Join-Path $script:ReleaseRoot "FireDM") "firedm.exe"
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw "Packaged executable missing for smoke check: $exe"
    }
    Invoke-CheckedCommand -Stage "smoke" -Command $exe -Arguments @("--help")
    Invoke-CheckedCommand -Stage "smoke" -Command $exe -Arguments @("--imports-only")
    Write-Log "Full Tk GUI smoke is headless-gated and requires manual verification."
}

function Add-ChangelogSource {
    param(
        [Parameter(Mandatory = $true)][object]$Sections,
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$Label = ""
    )

    $full = Resolve-RepoPath -Path $Path
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $name = $Path
        if ($Label) {
            $name = $Label
        }
        $script:ChangelogSources.Add([pscustomobject]@{ path = $Path; status = "included" }) | Out-Null
        $Sections.Add("## Source: $name") | Out-Null
        $Sections.Add("") | Out-Null
        $Sections.Add((Get-Content -LiteralPath $full -Raw)) | Out-Null
        $Sections.Add("") | Out-Null
    } else {
        $script:ChangelogSources.Add([pscustomobject]@{ path = $Path; status = "unavailable" }) | Out-Null
    }
}

function Write-CompiledChangelog {
    Write-Log "Stage 7 changelog compilation"
    $sections = New-Object System.Collections.Generic.List[string]
    $sections.Add("# FireDM Compiled Changelog") | Out-Null
    $sections.Add("") | Out-Null
    $sections.Add("- status: generated by root windows-build.ps1") | Out-Null
    $sections.Add("- build_id: $($script:ResolvedBuildId)") | Out-Null
    $sections.Add("- version: $($script:ResolvedVersion)") | Out-Null
    $sections.Add("- validation_status: see manifest.json validation_results") | Out-Null
    $sections.Add("") | Out-Null

    Add-ChangelogSource -Sections $sections -Path "ChangeLog.txt"
    Add-ChangelogSource -Sections $sections -Path "CHANGELOG.md"
    Add-ChangelogSource -Sections $sections -Path "RELEASE_NOTES.md"
    foreach ($path in Get-ChildItem -LiteralPath (Join-Path $script:RepoRoot "docs\release") -Filter "*.md" -File -ErrorAction SilentlyContinue | Sort-Object FullName) {
        Add-ChangelogSource -Sections $sections -Path (Get-RelativePath -BasePath $script:RepoRoot -Path $path.FullName)
    }
    # Debug handoff only in Debug mode
    if ($Mode -eq "Debug") {
        Add-ChangelogSource -Sections $sections -Path "docs\agent\SESSION_HANDOFF.md" -Label "agent session handoff"
    }

    if ($script:GitState.git_present) {
        $sections.Add("## Source: git log") | Out-Null
        $sections.Add("") | Out-Null
        $tag = Get-GitValue -Arguments @("describe", "--tags", "--abbrev=0")
        if ($tag) {
            $log = Get-GitValue -Arguments @("log", "$tag..HEAD", "--oneline", "--max-count=50")
        } else {
            $log = Get-GitValue -Arguments @("log", "--oneline", "--max-count=50")
        }
        if ($log) {
            $sections.Add($log) | Out-Null
        } else {
            $sections.Add("No git log entries available for the selected range.") | Out-Null
        }
        $sections.Add("") | Out-Null
        $script:ChangelogSources.Add([pscustomobject]@{ path = "git log"; status = "included" }) | Out-Null

        if ($script:GitState.dirty_tree) {
            $sections.Add("## Source: dirty working tree") | Out-Null
            $sections.Add("") | Out-Null
            $sections.Add($script:GitState.status_short) | Out-Null
            $sections.Add("") | Out-Null
        }
    } else {
        $script:ChangelogSources.Add([pscustomobject]@{ path = "git log"; status = "blocked" }) | Out-Null
    }

    $seenHeadings = @{}
    $deduped = New-Object System.Collections.Generic.List[string]
    foreach ($line in (($sections -join "`n") -split "`r?`n")) {
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#")) {
            if ($seenHeadings.ContainsKey($trimmed)) {
                continue
            }
            $seenHeadings[$trimmed] = $true
        }
        $deduped.Add($line) | Out-Null
    }

    $path = Join-Path $script:ReleaseRoot "CHANGELOG-COMPILED.md"
    Set-Content -LiteralPath $path -Value ($deduped -join "`n") -Encoding UTF8
}

function Get-ReleaseFileRecords {
    $records = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $script:ReleaseRoot)) {
        return $records
    }
    foreach ($path in Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Recurse -Force | Sort-Object FullName) {
        $relative = Get-RelativePath -BasePath $script:ReleaseRoot -Path $path.FullName
        $records.Add([pscustomobject]@{
            path = $relative.Replace("\", "/")
            size = $path.Length
        }) | Out-Null
    }
    return $records
}

function Get-ReleaseHashMap {
    $hashes = [ordered]@{}
    if (-not (Test-Path -LiteralPath $script:ReleaseRoot)) {
        return $hashes
    }
    foreach ($path in Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Recurse -Force | Sort-Object FullName) {
        $relative = (Get-RelativePath -BasePath $script:ReleaseRoot -Path $path.FullName).Replace("\", "/")
        if ($relative -in @("manifest.json", "checksums.sha256", "build.log")) {
            continue
        }
        $hashes[$relative] = (Get-FileHash -LiteralPath $path.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $hashes
}

function Write-Manifest {
    param([Parameter(Mandatory = $true)][object]$Hashes)

    Write-Log "Stage 8 manifest generation"
    $validationCommands = @()
    foreach ($result in $script:ValidationResults) {
        $validationCommands += [string]$result.command
    }
    $hashTable = [ordered]@{}
    foreach ($entry in $Hashes.GetEnumerator()) {
        $hashTable[[string]$entry.Key] = [string]$entry.Value
    }
    $pythonVersionText = (& $script:PythonPath --version 2>&1 | Out-String).Trim()
    $entryPointRelative = (Get-RelativePath -BasePath $script:RepoRoot -Path $script:EntryPoint).Replace("\", "/")
    $specFileRelative = (Get-RelativePath -BasePath $script:RepoRoot -Path $script:SpecFile).Replace("\", "/")
    $releaseFiles = @(Get-ReleaseFileRecords)
    $validationResults = @($script:ValidationResults.ToArray())
    $cleanupActions = @($script:CleanupActions.ToArray())
    $changelogSources = @($script:ChangelogSources.ToArray())
    $releaseArtifacts = @($script:ReleaseArtifacts.ToArray())
    $warningItems = @($script:Warnings.ToArray())
    $blockedItems = @($script:BlockedItems.ToArray())
    $included = @()
    $blocked = @()
    $planned = @()
    $discoveryWarnings = @()
    if ($script:PluginManifest) {
        if ($script:PluginManifest.included) { $included = @($script:PluginManifest.included) }
        if ($script:PluginManifest.blocked) { $blocked = @($script:PluginManifest.blocked) }
        if ($script:PluginManifest.planned) { $planned = @($script:PluginManifest.planned) }
        if ($script:PluginManifest.discovery_warnings) { $discoveryWarnings = @($script:PluginManifest.discovery_warnings) }
    }
    $includedDeps = @("pycurl", "yt-dlp", "Pillow", "pystray", "awesometkinter", "plyer", "certifi", "packaging")
    $manifest = [ordered]@{
        app_name = "FireDM"
        app_version = $script:ResolvedVersion
        build_id = $script:ResolvedBuildId
        build_time_utc = (Get-Date).ToUniversalTime().ToString("o")
        repo_root = $script:RepoRoot
        git_present = $script:GitState.git_present
        git_branch = $script:GitState.git_branch
        git_commit = $script:GitState.git_commit
        dirty_tree = $script:GitState.dirty_tree
        python_version = $pythonVersionText
        powershell_version = $PSVersionTable.PSVersion.ToString()
        os_version = [System.Environment]::OSVersion.VersionString
        gui_backend = $script:GuiBackend
        gui_entry_point = $script:GuiEntryPoint
        build_backend = $script:BuildBackend
        build_kind = $Kind
        build_mode = $Mode
        channel = $Channel
        arch = $Arch
        entry_point = $entryPointRelative
        spec_file = $specFileRelative
        included_dependencies = $includedDeps
        included_plugins = $included
        blocked_plugins = $blocked
        planned_plugins = $planned
        plugin_discovery_warnings = $discoveryWarnings
        validation_commands = $validationCommands
        validation_results = $validationResults
        cleanup_actions = $cleanupActions
        changelog_sources = $changelogSources
        release_artifacts = $releaseArtifacts
        release_files = $releaseFiles
        sha256_hashes = $hashTable
        warnings = $warningItems
        blocked_items = $blockedItems
        compatibility = [ordered]@{
            root_windows_build_ps1 = "canonical"
            scripts_windows_build_ps1 = "thin wrapper"
            build_release_bat = "deleted in pre-existing dirty tree; not restored by this patch"
        }
    }

    $path = Join-Path $script:ReleaseRoot "manifest.json"
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
}

function Write-ReleaseChecksums {
    Write-Log "Stage 9 checksum generation"
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($path in Get-ChildItem -LiteralPath $script:ReleaseRoot -File -Recurse -Force | Sort-Object FullName) {
        $relative = (Get-RelativePath -BasePath $script:ReleaseRoot -Path $path.FullName).Replace("\", "/")
        if ($relative -eq "checksums.sha256") {
            continue
        }
        $hash = (Get-FileHash -LiteralPath $path.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $lines.Add("$hash  $relative") | Out-Null
    }
    if ($lines.Count -eq 0) {
        throw "No release files available for checksum generation."
    }
    Set-Content -LiteralPath (Join-Path $script:ReleaseRoot "checksums.sha256") -Value ($lines -join "`n") -Encoding ASCII
}

try {
    if ($Clean -and $NoClean) {
        throw "Use only one of -Clean or -NoClean."
    }

    $script:ReleaseRoot = Resolve-RepoPath -Path $OutputDir
    if (-not (Test-UnderRepo $script:ReleaseRoot)) {
        throw "OutputDir must stay inside repo root: $script:ReleaseRoot"
    }
    New-Item -ItemType Directory -Path $script:ReleaseRoot -Force | Out-Null
    $script:BuildLog = Join-Path $script:ReleaseRoot "build.log"
    Set-Content -LiteralPath $script:BuildLog -Value "FireDM Windows build log" -Encoding UTF8

    Write-Log "Stage 0 bootstrap"
    Write-Log "repo_root=$script:RepoRoot"
    Write-Log "release_root=$script:ReleaseRoot"

    $script:Tools = @{
        python = Find-Tool "python"
        git = Find-Tool "git"
        pyinstaller = Find-Tool "pyinstaller"
        nuitka = Find-Tool "nuitka"
        ffmpeg = Find-Tool "ffmpeg"
        ffprobe = Find-Tool "ffprobe"
    }
    $script:PythonPath = Resolve-Python
    $script:ResolvedVersion = Get-AppVersion
    $script:ResolvedBuildId = Get-DefaultBuildId

    Write-Log "python=$script:PythonPath"
    Write-Log "version=$script:ResolvedVersion build_id=$script:ResolvedBuildId mode=$Mode"
    if ($Release) {
        Add-BuildWarning "legacy-release-switch" "-Release is accepted for compatibility; use -Mode Release on the canonical script."
    }

    Write-Log "Stage 1 repo state snapshot"
    $script:GitState = Get-RepoState
    if ($script:GitState.git_present) {
        Write-Log "git branch=$($script:GitState.git_branch) commit=$($script:GitState.git_commit) dirty=$($script:GitState.dirty_tree)"
    } else {
        Add-BlockedItem "git-unavailable" $script:GitState.status_short
    }

    Write-Log "Stage 2 cleanup crew"
    $cleanupPlan = Get-CleanupPlan
    Invoke-CleanupPlan $cleanupPlan

    Invoke-DependencyChecks           # Stage 3: tools, entry points, backend selection
    Invoke-BuildInfoStamp              # Stage 4: stamp firedm/_build_info.py
    Invoke-QA                          # Stage 5: compile, lint, type-check, tests
    Invoke-PythonDistributionBuild     # Stage 5b: wheel and source distribution under release
    Get-PluginManifestSection          # Stage 6: discover plugin manifest
    Write-PluginManifestArtifacts       # Stage 6a: write plugin manifest artifacts
    Invoke-PackageBuild                # Stage 7: PyInstaller one-folder
    Test-ArtifactIntegrity             # Stage 8: verify EXE sizes and presence
    Invoke-SmokeCheck                  # Stage 9: packaged CLI smoke
    Write-CompiledChangelog            # Stage 10: compile CHANGELOG-COMPILED.md
    $hashes = Get-ReleaseHashMap
    Write-Manifest $hashes             # Stage 11: manifest.json
    Write-ReleaseChecksums             # Stage 12: checksums.sha256

    Write-BuildSummary
    Write-Host "Release output: $script:ReleaseRoot"
    Write-Host "Manifest       : $(Join-Path $script:ReleaseRoot 'manifest.json')"
    Write-Host "Changelog      : $(Join-Path $script:ReleaseRoot 'CHANGELOG-COMPILED.md')"
    Write-Host "Checksums      : $(Join-Path $script:ReleaseRoot 'checksums.sha256')"
    Write-Host "Build log      : $script:BuildLog"
    exit 0
} catch {
    $message = $_.Exception.Message
    if ($script:BuildLog) {
        Write-Log $message "ERROR"
        if ($_.ScriptStackTrace) {
            Write-Log $_.ScriptStackTrace "ERROR"
        }
        if ($_.InvocationInfo -and $_.InvocationInfo.PositionMessage) {
            Write-Log $_.InvocationInfo.PositionMessage "ERROR"
        }
    } else {
        Write-Host "[ERROR] $message"
    }
    exit 1
}
