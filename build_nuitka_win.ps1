<#
.SYNOPSIS
    Build "WiFi Led Studio.exe" with Nuitka (standalone) on Windows.

.DESCRIPTION
    Compiles WiFi Led Studio into a standalone Windows executable with all
    required dependencies, metadata, icons, and web frontend assets bundled.

.PARAMETER Python
    Path to Python executable. If omitted, uses $env:PYTHON, the 'wls' conda env
    (if present), or the default 'python' in PATH.

.PARAMETER OutDir
    Output directory for the build artifacts. Defaults to "dist_nuitka".

.PARAMETER AppName
    Application name. Defaults to "WiFi Led Studio".

.PARAMETER Console
    If specified, builds with console window enabled (useful for debugging).
    Default is disabled (Win32 background/tray application).

.PARAMETER Clean
    If specified, deletes previous build artifacts before building.

.PARAMETER Zip
    If specified, packages the dist folder into a zip archive (WiFi-Led-Studio-Windows.zip).

.PARAMETER SmokeTest
    If specified, runs the built executable with --ci-smoke-test to verify functionality.

.EXAMPLE
    .\build_nuitka_win.ps1
    .\build_nuitka_win.ps1 -Console -SmokeTest
    .\build_nuitka_win.ps1 -Clean -Zip
#>

[CmdletBinding()]
param(
    [string]$Python = "",
    [string]$OutDir = "dist_nuitka",
    [string]$AppName = "WiFi Led Studio",
    [switch]$Console,
    [switch]$Clean,
    [switch]$Zip,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    WiFi Led Studio - Nuitka Windows Build System        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Resolve Python executable
if (-not $Python) {
    if ($env:PYTHON -and (Test-Path $env:PYTHON)) {
        $Python = $env:PYTHON
    } elseif (Test-Path "D:\CondaData\envs\wls\python.exe") {
        $Python = "D:\CondaData\envs\wls\python.exe"
    } else {
        $pyCmd = Get-Command "python.exe" -ErrorAction SilentlyContinue
        if ($pyCmd) {
            $Python = $pyCmd.Source
        } else {
            Write-Error "Python executable not found. Please specify -Python or add python to PATH."
            exit 1
        }
    }
}

Write-Host "[1/6] Using Python: $Python" -ForegroundColor Green
& $Python --version

# 2. Extract Version Info from wls.consts
$version = "3.5.0"
try {
    $versionOutput = & $Python -c "import sys; sys.path.insert(0, '.'); from wls.consts import PROJECT_VERSION; print(PROJECT_VERSION)"
    if ($versionOutput) {
        $version = $versionOutput.Trim()
    }
} catch {
    Write-Warning "Could not extract PROJECT_VERSION dynamically, using default: $version"
}

# Format to 4-part version for Windows resource (e.g. 3.5.0.0)
$cleanVersion = ($version -split '-')[0]
$vParts = [System.Collections.Generic.List[string]]($cleanVersion.Split('.'))
while ($vParts.Count -lt 4) { $vParts.Add("0") }
$fileVersion = ($vParts[0..3] -join '.')
$productVersion = $fileVersion

Write-Host "[2/6] Target version: $version (Windows resource: $fileVersion)" -ForegroundColor Green

# 3. Clean if requested
if ($Clean) {
    Write-Host "[3/6] Cleaning previous build artifacts in '$OutDir'..." -ForegroundColor Yellow
    if (Test-Path $OutDir) {
        Remove-Item -Recurse -Force $OutDir -ErrorAction SilentlyContinue
    }
    Remove-Item -Force "WiFi-Led-Studio-Windows.zip" -ErrorAction SilentlyContinue
    Remove-Item -Force "nuitka-crash-report.xml" -ErrorAction SilentlyContinue
} else {
    Write-Host "[3/6] Skipping clean (use -Clean to perform clean build)" -ForegroundColor Gray
}

# 4. Check & Install/Upgrade Nuitka build tools
Write-Host "[4/6] Verifying Nuitka and dependencies..." -ForegroundColor Green
& $Python -m pip install -U -q nuitka ordered-set zstandard

# Determine console mode
$consoleMode = if ($Console) { "force" } else { "disable" }
Write-Host "      Windows Console Mode: $consoleMode" -ForegroundColor Cyan

# 5. Execute Nuitka compilation
Write-Host "[5/6] Running Nuitka standalone compiler..." -ForegroundColor Green

$nuitkaArgs = @(
    "-m", "nuitka",
    "--standalone",
    "--assume-yes-for-downloads",
    "--output-dir=$OutDir",
    "--output-filename=$AppName.exe",
    "--windows-console-mode=$consoleMode",
    "--windows-icon-from-ico=icons/wifiledstudio.ico",
    "--company-name=Rainbow Music Led",
    "--product-name=WiFi Led Studio",
    "--file-version=$fileVersion",
    "--product-version=$productVersion",
    "--file-description=WiFi Led Studio @ Rainbow Music Led",
    "--copyright=© 2025 Rainbow Music Led",
    "--include-package=wls",
    "--include-package=wls_frontend",
    "--include-package=pynput",
    "--include-package=pystray",
    "--include-package=sentry_sdk",
    "--include-package=pycaw",
    "--include-package=comtypes",
    "--include-package=aubio",
    "--nofollow-import-to=*.tests",
    "--nofollow-import-to=*.test",
    "--nofollow-import-to=unittest",
    "--include-package-data=wls",
    "--include-package-data=bokeh",
    "--include-package-data=xyzservices",
    "--include-data-dir=wls_frontend=wls_frontend",
    "--include-data-dir=icons=icons",
    "--include-data-files=icons/tray.png=tray.png",
    "wls/__main__.py"
)

& $Python @nuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Nuitka compilation failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

# 6. Normalize output directory structure
# Nuitka may create "__main__.dist" or "$AppName.dist"
$targetDist = Join-Path $OutDir $AppName
$candidateDirs = @(
    (Join-Path $OutDir "__main__.dist"),
    (Join-Path $OutDir "$AppName.dist")
)

foreach ($dir in $candidateDirs) {
    if (Test-Path $dir) {
        if ($dir -ne $targetDist) {
            if (Test-Path $targetDist) {
                Remove-Item -Recurse -Force $targetDist
            }
            Write-Host "Normalizing dist folder: $dir -> $targetDist" -ForegroundColor Cyan
            Rename-Item -Path $dir -NewName $AppName
        }
        break
    }
}

$exePath = Join-Path $targetDist "$AppName.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "Executable not found at expected path: $exePath"
    exit 1
}

# Ensure tray icon is also directly accessible in root & icons dir
if (Test-Path "icons\tray.png") {
    Copy-Item -Path "icons\tray.png" -Destination (Join-Path $targetDist "tray.png") -Force -ErrorAction SilentlyContinue
    $targetIcons = Join-Path $targetDist "icons"
    if (-not (Test-Path $targetIcons)) {
        New-Item -ItemType Directory -Path $targetIcons | Out-Null
    }
    Copy-Item -Path "icons\*" -Destination $targetIcons -Force -Recurse -ErrorAction SilentlyContinue
}

# Copy delvewheel DLLs (.libs) directly into executable root to ensure 100% DLL resolution on Windows
Get-ChildItem -Path $targetDist -Filter "*.libs" -Directory | ForEach-Object {
    Write-Host "Copying vendor DLLs from $($_.Name) to application root..." -ForegroundColor Cyan
    Copy-Item -Path (Join-Path $_.FullName "*") -Destination $targetDist -Force -ErrorAction SilentlyContinue
}

# Copy Conda environment runtime DLLs (ffi.dll, libcrypto, etc.) if running in Conda
$pyDir = Split-Path -Parent $Python
$condaLibBin = Join-Path $pyDir "Library\bin"
if (Test-Path $condaLibBin) {
    Write-Host "Detecting Conda environment: copying runtime DLLs from $condaLibBin to application root..." -ForegroundColor Cyan
    Get-ChildItem -Path $condaLibBin -Filter "*.dll" | ForEach-Object {
        $destFile = Join-Path $targetDist $_.Name
        if (-not (Test-Path $destFile)) {
            Copy-Item -Path $_.FullName -Destination $destFile -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "    Build Successful!" -ForegroundColor Green
Write-Host "    Executable: $exePath" -ForegroundColor Green
$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "    Exe Size  : $([math]::Round($exeSize, 2)) MB" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""

# Optional Smoke Test
if ($SmokeTest) {
    Write-Host "[Smoke Test] Running 5-second sanity check with --ci-smoke-test..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath $exePath -ArgumentList "--ci-smoke-test" -PassThru -Wait
    if ($proc.ExitCode -eq 0) {
        Write-Host "[Smoke Test] PASSED: Executable started and exited cleanly." -ForegroundColor Green
    } else {
        Write-Warning "[Smoke Test] Process exited with code $($proc.ExitCode)"
    }
}

# Optional Zip Packaging
if ($Zip) {
    $zipPath = Join-Path $ScriptDir "WiFi-Led-Studio-Windows.zip"
    Write-Host "Packaging build into $zipPath..." -ForegroundColor Cyan
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }
    Compress-Archive -Path $targetDist -DestinationPath $zipPath
    Write-Host "Archive created successfully: $zipPath" -ForegroundColor Green
}
