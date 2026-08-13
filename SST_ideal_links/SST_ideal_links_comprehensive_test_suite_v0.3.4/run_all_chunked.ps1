param(
  [ValidateSet("quick","full","max")]
  [string]$Preset = "full",
  [string]$Output = "",
  [switch]$AllDatabase,
  [string[]]$Ids = @(),
  [int]$NativeThreads = 0,
  [int]$Retries = 2,
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = if (Test-Path "$Root\.venv\Scripts\python.exe") {
  "$Root\.venv\Scripts\python.exe"
} else {
  "python"
}
$InputFile = "$Root\data\idealLinks.txt"
$ConfigFile = "$Root\configs\$Preset.json"
if ($Output -eq "") { $Output = "$Root\outputs_$Preset" }
New-Item -ItemType Directory -Force -Path $Output | Out-Null

$DefaultIds = @(
  "L2a1","L4a1","L5a1",
  "L6a1","L6a2","L6a3","L6a4","L6a5","L6n1",
  "L7a1","L7a2","L7a3","L7a4","L7a5","L7a6","L7a7","L7n1","L7n2"
)
if ($Ids.Count -gt 0) {
  $SelectedIds = $Ids
} elseif ($AllDatabase) {
  $Lines = & $Python -m sst_link_suite.cli list --input $InputFile
  if ($LASTEXITCODE -ne 0) { throw "Could not list database links." }
  $SelectedIds = @($Lines | ForEach-Object { ($_ -split "`t")[0] })
} else {
  $SelectedIds = $DefaultIds
}

if ($NativeThreads -gt 0) {
  $env:SST_NATIVE_MAX_THREADS = "$NativeThreads"
}

Write-Host "Building strict native backend..."
& $Python -m sst_link_suite.cli build-native --strict
if ($LASTEXITCODE -ne 0) { throw "Native build failed." }

$First = $true
$Ledger = @()
foreach ($LinkId in $SelectedIds) {
  $Success = $false
  for ($Attempt = 1; $Attempt -le ($Retries + 1); $Attempt++) {
    Write-Host "[$LinkId] attempt $Attempt"
    $ArgsList = @(
      "-m", "sst_link_suite.cli", "run",
      "--input", $InputFile,
      "--output", $Output,
      "--config", $ConfigFile,
      "--ids", $LinkId,
      "--require-native",
      "--defer-report"
    )
    if (-not $First) { $ArgsList += "--skip-parity" }
    if ($NoResume -and $Attempt -eq 1) { $ArgsList += "--no-resume" }
    if ($NativeThreads -gt 0) { $ArgsList += @("--native-threads", "$NativeThreads") }

    $Started = Get-Date
    & $Python @ArgsList
    $Code = $LASTEXITCODE
    $Elapsed = ((Get-Date) - $Started).TotalSeconds
    $Ledger += [pscustomobject]@{
      link_id = $LinkId
      attempt = $Attempt
      returncode = $Code
      elapsed_s = $Elapsed
    }
    if ($Code -eq 0) {
      $Success = $true
      $First = $false
      break
    }
    Write-Warning "$LinkId failed with exit code $Code; retrying."
  }
  if (-not $Success) {
    $Ledger | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "$Output\powershell_chunk_ledger.json"
    throw "Campaign stopped: $LinkId failed after $($Retries + 1) attempts."
  }
  $Ledger | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "$Output\powershell_chunk_ledger.json"
}

Write-Host "Rebuilding combined tables and report..."
$RebuildArgs = @(
  "-m", "sst_link_suite.cli", "rebuild-report",
  "--input", $InputFile,
  "--output", $Output,
  "--config", $ConfigFile,
  "--ids"
) + $SelectedIds
& $Python @RebuildArgs
if ($LASTEXITCODE -ne 0) { throw "Combined report rebuild failed." }

Write-Host "Completed $($SelectedIds.Count) links. Output: $Output"
