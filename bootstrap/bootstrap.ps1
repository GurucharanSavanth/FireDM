param(
    [string]$PythonExe,
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Resolve-Python {
    param([string]$Requested)

    if ($Requested) {
        return (Resolve-Path $Requested).Path
    }

    $launcherPython = & py -3.10 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -eq 0 -and $launcherPython) {
        return $launcherPython.Trim()
    }

    $fallback = Get-Command python -ErrorAction SilentlyContinue
    if ($fallback) {
        return $fallback.Source
    }

    throw "Python 3.10 was not found. Install it first or pass -PythonExe."
}

function Normalize-Text {
    param([object]$Value)

    return (($Value | Out-String).Trim())
}

function Resolve-FFmpeg {
    $command = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $wingetPath = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetPath) {
        $found = Get-ChildItem $wingetPath -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) {
            return $found
        }
    }

    return ""
}

$PythonExe = Resolve-Python -Requested $PythonExe
$VenvPath = (Join-Path $RepoRoot $VenvPath)
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$ManifestPath = Join-Path $PSScriptRoot "environment-manifest.json"

Write-Host "Using Python:" $PythonExe
Write-Host "Repo root:" $RepoRoot
Write-Host "Venv path:" $VenvPath
Write-Host "Setting current-process PYTHONUTF8=1 for consistent UTF-8 behavior."
$env:PYTHONUTF8 = "1"

if (-not (Test-Path $VenvPython)) {
    & $PythonExe -m venv $VenvPath
}

& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install -e ".[dev,build]"

$pythonVersion = Normalize-Text (& $VenvPython --version 2>&1)
$pipVersion = Normalize-Text (& $VenvPython -m pip --version 2>&1)
$gitVersion = Normalize-Text (& git --version 2>&1)
$ffmpegPath = Resolve-FFmpeg
$ffmpegVersion = if ($ffmpegPath) { Normalize-Text ((& $ffmpegPath -version)[0]) } else { "" }
$pycurlVersion = Normalize-Text (& $VenvPython -c "import pycurl; print(pycurl.version)" 2>&1)

& $VenvPython -m pytest -q
& $VenvPython -m firedm --help | Out-Null
& $VenvPython firedm.py --imports-only | Out-Null

$manifest = [ordered]@{
    generated_on = (Get-Date).ToString("yyyy-MM-dd")
    repo_root = $RepoRoot
    python = @{
        executable = $VenvPython
        version = $pythonVersion
        pip = $pipVersion
    }
    git = @{
        version = $gitVersion
    }
    ffmpeg = @{
        path = $ffmpegPath
        version = $ffmpegVersion
    }
    env = @{
        PYTHONUTF8 = "1 (current process)"
    }
    pycurl = @{
        version = $pycurlVersion
    }
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $ManifestPath -Encoding utf8
Write-Host "Bootstrap complete. Manifest written to $ManifestPath"
