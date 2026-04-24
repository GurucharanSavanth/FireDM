param(
    [string]$PythonExe,
    [switch]$SkipTests,
    [switch]$SmokeGui
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

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

$PythonExe = Resolve-Python -Requested $PythonExe
Write-Host "Using Python:" $PythonExe

Invoke-Checked $PythonExe @("-m", "pip", "install", "--no-build-isolation", "-e", ".[build]")

if (-not $SkipTests) {
    Invoke-Checked $PythonExe @("-m", "pytest", "-q")
    Invoke-Checked $PythonExe @("-m", "build", "--no-isolation")
}

$DistFireDM = Join-Path $RepoRoot "dist\FireDM"
Get-Process | Where-Object {
    try {
        $_.Path -and $_.Path.StartsWith($DistFireDM, [System.StringComparison]::OrdinalIgnoreCase)
    }
    catch {
        $false
    }
} | ForEach-Object {
    Write-Host "Stopping running packaged process:" $_.Id $_.ProcessName
    Stop-Process -Id $_.Id -Force
}

Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\dist\FireDM" -Recurse -Force -ErrorAction SilentlyContinue

Invoke-Checked $PythonExe @("-m", "PyInstaller", "--clean", "--noconfirm", ".\scripts\firedm-win.spec")
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

if ($SmokeGui) {
    $process = Start-Process -FilePath ".\dist\FireDM\FireDM-GUI.exe" -PassThru
    Start-Sleep -Seconds 5
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id
    }
}

Write-Host "Packaged build ready at .\dist\FireDM"
