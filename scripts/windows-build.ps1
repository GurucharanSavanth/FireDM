[CmdletBinding()]
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
    [string]$OutputDir,
    [string]$Version,
    [string]$PythonExe,
    [string]$Channel,
    [ValidateSet("x64", "x86", "arm64")]
    [string]$Arch,
    [string]$BuildId,
    [string]$BuildDate,
    [switch]$AllowOverwrite,
    [switch]$SkipLint,
    [switch]$SkipPythonPackage,
    [switch]$SkipTwineCheck,
    [switch]$PayloadOnly,
    [switch]$ValidateOnly,
    [switch]$InstallLocalDeps,
    [switch]$SmokeGui,
    [switch]$Release,
    [string]$ReleaseDir,
    [switch]$PublishDraftRelease,
    [string]$GithubRepo,
    [string]$GithubTag
)

$rootScript = Join-Path (Split-Path -Parent $PSScriptRoot) "windows-build.ps1"
if (-not (Test-Path -LiteralPath $rootScript -PathType Leaf)) {
    Write-Error "Canonical Windows build script missing: $rootScript"
    exit 1
}

$forward = @{}
foreach ($key in $PSBoundParameters.Keys) {
    $forward[$key] = $PSBoundParameters[$key]
}

& $rootScript @forward
exit $LASTEXITCODE
