$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m venv .venv
& "$ProjectRoot\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$ProjectRoot\.venv\Scripts\python.exe" -m pip install -e .

Write-Host "Bootstrap complete."
Write-Host "Update configs\candidate_profile.yaml and configs\settings.yaml before turning on email delivery."
