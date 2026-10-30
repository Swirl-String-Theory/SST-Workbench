# Read-only fallback for an already running v0.2.5 without an integrated heartbeat.
param([int]$IntervalSeconds=10)
if ($IntervalSeconds -lt 1) { throw 'IntervalSeconds must be >=1' }
$proj = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Write-Host "A075 read-only process monitor. Ctrl+C to exit. No progress percentage available for old run."
while ($true) {
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $targets = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|sst_sycl_worker' -and $_.CommandLine -match 'A075|run_instance|run_all' }
    if (-not $targets) { Write-Host "[$stamp] No matching A075 Python processes; check actual command line and other shells." }
    foreach ($item in $targets) {
        try { $p = Get-Process -Id $item.ProcessId -ErrorAction Stop
            Write-Host "[$stamp] PID=$($p.Id) name=$($p.ProcessName) total_CPU_s=$([math]::Round($p.CPU,1)) memory_GB=$([math]::Round($p.WorkingSet64/1GB,2))"
        } catch { Write-Host "[$stamp] PID=$($item.ProcessId) process not readable" }
    }
    Get-ChildItem -Path (Split-Path -Parent $proj) -Directory -Filter 'A075-v0.2.*' -ErrorAction SilentlyContinue |
      ForEach-Object { Get-ChildItem $_.FullName -Recurse -File -Include '*energy_matrix.csv','*step_energy.csv','GATE_LEDGER.json' -ErrorAction SilentlyContinue } |
      Sort-Object LastWriteTime -Descending | Select-Object -First 3 |
      ForEach-Object { Write-Host "[$stamp] last output: $($_.LastWriteTime) $($_.FullName)" }
    Start-Sleep -Seconds $IntervalSeconds
}
