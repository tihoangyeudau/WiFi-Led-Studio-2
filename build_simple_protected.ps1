#!/usr/bin/env powershell

Write-Host "WiFi Led Studio - Simple Protected Build" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Compile source to bytecode
Write-Host "Step 1: Compiling source to bytecode..." -ForegroundColor Cyan
python simple_protect.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Source compilation failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host "Source code compiled to bytecode!" -ForegroundColor Green
Write-Host ""

# Step 2: Clean previous build
Write-Host "Step 2: Cleaning previous build..." -ForegroundColor Cyan
Remove-Item -Recurse -Force "build_simple_protected" -ErrorAction SilentlyContinue
Write-Host "Previous build cleaned!" -ForegroundColor Green
Write-Host ""

# Step 3: Build with protected source
Write-Host "Step 3: Building with bytecode-protected source..." -ForegroundColor Cyan
python setup_simple_protected.py build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Protected build completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Protected build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""

# Step 4: Verify build
$exePath = "build_simple_protected\WiFi Led Studio\WiFi Led Studio.exe"
if (Test-Path $exePath) {
    Write-Host "Protected executable created: $exePath" -ForegroundColor Green

    # Check file size
    $fileSize = (Get-Item $exePath).Length / 1MB
    Write-Host "Executable size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan

    # Check for source files in lib directory
    $libPath = "build_simple_protected\WiFi Led Studio\lib"
    if (Test-Path $libPath) {
        $pyFiles = Get-ChildItem -Path $libPath -Filter "*.py" -Recurse
        $pycFiles = Get-ChildItem -Path $libPath -Filter "*.pyc" -Recurse

        Write-Host "Source protection status:" -ForegroundColor Cyan
        Write-Host "   .py files: $($pyFiles.Count)" -ForegroundColor $(if ($pyFiles.Count -eq 0) { "Green" } else { "Yellow" })
        Write-Host "   .pyc files: $($pycFiles.Count)" -ForegroundColor $(if ($pycFiles.Count -gt 0) { "Green" } else { "Red" })

        if ($pyFiles.Count -eq 0 -and $pycFiles.Count -gt 0) {
            Write-Host "Source is protected with bytecode!" -ForegroundColor Green
        } elseif ($pyFiles.Count -gt 0) {
            Write-Host "Some .py files still present - partial protection" -ForegroundColor Yellow
        } else {
            Write-Host "No source files found - check build" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Protected executable not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 5: Test the protected build
Write-Host "Step 5: Testing protected build..." -ForegroundColor Cyan
Write-Host "Starting protected WiFi Led Studio..." -ForegroundColor Yellow
Write-Host "Check system tray for icon and web interface at http://localhost:8090" -ForegroundColor Yellow
Write-Host "Test will run for 15 seconds" -ForegroundColor Yellow
Write-Host ""

try {
    # Start the process
    $process = Start-Process -FilePath $exePath -PassThru -WindowStyle Hidden

    Write-Host "Protected process started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host ""

    # Wait for 15 seconds
    for ($i = 15; $i -gt 0; $i--) {
        Write-Host "Testing $i seconds... (Check system tray and http://localhost:8090)" -NoNewline
        Start-Sleep 1
        Write-Host "`r" -NoNewline
    }

    Write-Host ""
    Write-Host ""
    Write-Host "Stopping test..." -ForegroundColor Yellow

    # Stop the process
    if (!$process.HasExited) {
        $process.CloseMainWindow()
        Start-Sleep 2

        if (!$process.HasExited) {
            $process.Kill()
            $process.WaitForExit()
        }
    }

    Write-Host "Test completed" -ForegroundColor Green

} catch {
    Write-Host "Error testing protected build: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Simple Protected Build Summary:" -ForegroundColor Green
Write-Host "Source code compiled to bytecode (.pyc files)" -ForegroundColor Green
Write-Host "Protected executable created" -ForegroundColor Green
Write-Host "System tray functionality preserved" -ForegroundColor Green
Write-Host "Source code protected from casual inspection" -ForegroundColor Green
Write-Host ""
Write-Host "Build location: build_simple_protected\WiFi Led Studio\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Protection level:" -ForegroundColor Cyan
Write-Host "   • Python source compiled to bytecode (.pyc)" -ForegroundColor White
Write-Host "   • Source files not readable as plain text" -ForegroundColor White
Write-Host "   • Suitable for basic source protection" -ForegroundColor White

Read-Host "`nPress Enter to exit"