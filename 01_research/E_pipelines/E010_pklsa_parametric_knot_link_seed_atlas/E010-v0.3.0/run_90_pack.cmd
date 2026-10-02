@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "$o='SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs'; if(Test-Path $o){$z=Join-Path '..' ($o+'.zip'); if(Test-Path $z){Remove-Item $z -Force}; Compress-Archive -Path $o -DestinationPath $z -CompressionLevel Optimal; Get-FileHash $z -Algorithm SHA256 ^| Format-List} else {Write-Error 'Output directory not found'; exit 2}"
endlocal
