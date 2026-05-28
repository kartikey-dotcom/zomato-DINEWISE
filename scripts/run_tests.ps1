# Run all unit tests; use -Live for Gemini API test
param(
    [switch]$Live
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Refresh PATH so newly installed Python is visible
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

$python = $null
foreach ($candidate in @(
    ".\.venv\Scripts\python.exe",
    "python",
    "python3",
    "py"
)) {
    if ($candidate -eq "py") {
        try {
            $ver = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($ver) { $python = $ver.Trim(); break }
        } catch { continue }
    } elseif ($candidate -match "^\\.|python") {
        if ($candidate -match "^\\.") {
            if (Test-Path $candidate) { $python = (Resolve-Path $candidate).Path; break }
        } else {
            $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($cmd -and $cmd.Source -notmatch "WindowsApps") {
                $python = $cmd.Source
                break
            }
        }
    }
}

if (-not $python) {
    Write-Host "Python not found. Install Python 3.11+ and run:"
    Write-Host "  python -m venv .venv"
    Write-Host "  .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}

Write-Host "Using: $python"
& $python -m pip install -r requirements.txt -q
& $python -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Live) {
    Write-Host "`n--- Live Gemini API test ---"
    & $python -m pytest tests/test_llm_live.py -v -m slow --tb=short
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python scripts/smoke_llm.py
}
