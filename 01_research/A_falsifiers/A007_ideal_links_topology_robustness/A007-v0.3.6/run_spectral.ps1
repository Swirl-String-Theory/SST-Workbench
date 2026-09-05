param([string[]]$Ids=@("L2a1","L4a1","L6a4","L6n1","L7n2"),[string]$Output="outputs_spectral")
Set-Location $PSScriptRoot
$Python=Join-Path $PSScriptRoot ".venv\Scripts\python.exe"; if(-not(Test-Path $Python)){$Python="python"}
$ArgsList=@("scripts\run_spectral.py","--config","configs\spectral_audit.json","--output",$Output)
if($Ids.Count -gt 0){$ArgsList+=@("--ids")+$Ids}
& $Python @ArgsList
exit $LASTEXITCODE
