param(
  [int]$ExcludePid = 0
)

$processes = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
  Where-Object {
    $_.CommandLine -like '*TATU_Ombor_bot*' -and
    $_.ProcessId -ne $ExcludePid
  }

if (-not $processes) {
  Write-Host "Ishlayotgan bot topilmadi."
  exit 0
}

foreach ($p in $processes) {
  Write-Host "To'xtatildi PID: $($p.ProcessId)"
  Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Tayyor. $($processes.Count) ta jarayon to'xtatildi."
