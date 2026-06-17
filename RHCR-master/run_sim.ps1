$success = $false
$attempts = 0
Remove-Item -Path "exp\kinematic_test\paths.txt" -ErrorAction SilentlyContinue
while (-not $success -and $attempts -lt 20) {
    $attempts++
    Write-Host "Attempt $attempts... (Running with 20 agents to prevent start deadlocks)"
    .\build\lifelong.exe --scenario KIVA --map maps/kiva_kinematic.map --task tasks.txt --out exp/kinematic_test --simulation_time 50 --simulation_window 5 --planning_window 10 --solver PBS --agentNum 20 --footprint_shape rect --footprint_width 1 --footprint_height 3
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Success on attempt $attempts!"
        $success = $true
    } else {
        Write-Host "Failed. Retrying..."
    }
}
