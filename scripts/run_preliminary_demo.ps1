$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

Write-Output "[1/3] Running normal account_lock scenario"
python -m app.cli --task-id demo-account-lock
if ($LASTEXITCODE -ne 0) {
    throw "Normal scenario failed with exit code $LASTEXITCODE"
}

Write-Output "[2/3] Running injected fake_success scenario"
python -m app.cli --fake-success --task-id demo-fake-success
if ($LASTEXITCODE -ne 1) {
    throw "Fake-success scenario should fail closed with exit code 1; got $LASTEXITCODE"
}

Write-Output "[3/3] Running test suite"
python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed with exit code $LASTEXITCODE"
}

Write-Output "Preliminary demo verification completed."
