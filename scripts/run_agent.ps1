$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Set-Location $ProjectRoot
& $Python -m jobgraph.cli run --project-root $ProjectRoot --settings "$ProjectRoot\configs\settings.yaml" --profile "$ProjectRoot\configs\candidate_profile.yaml" --companies "$ProjectRoot\configs\companies.yaml"
