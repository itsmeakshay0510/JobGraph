param(
    [string]$TaskPrefix = "JobGraph",
    [switch]$Force
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $ProjectRoot "scripts\run_agent.ps1"
$Command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Runner`""

Write-Host "Registering daily tasks at 11:00 and 17:00 using local machine time..."

$Args11 = @("/Create", "/SC", "DAILY", "/ST", "11:00", "/TN", "$TaskPrefix-11AM", "/TR", $Command)
$Args17 = @("/Create", "/SC", "DAILY", "/ST", "17:00", "/TN", "$TaskPrefix-5PM", "/TR", $Command)
if ($Force) {
    $Args11 += "/F"
    $Args17 += "/F"
}

& schtasks.exe @Args11
& schtasks.exe @Args17

Write-Host "Done. Use Task Scheduler to inspect or disable the tasks."
