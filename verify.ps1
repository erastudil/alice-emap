$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    python -m unittest discover -s tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
