$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Lib = Join-Path $Root 'lib'
New-Item -ItemType Directory -Force -Path $Lib | Out-Null

$Items = @(
    @{ Name='mathjs 15.2.0';       Url='https://unpkg.com/mathjs@15.2.0/lib/browser/math.js';                         File='math.js' },
    @{ Name='numeric 1.2.6';       Url='https://cdn.jsdelivr.net/npm/numeric@1.2.6/numeric-1.2.6.min.js';             File='numeric-1.2.6.min.js' },
    @{ Name='numeral 2.0.6';       Url='https://cdn.jsdelivr.net/npm/numeral@2.0.6/min/numeral.min.js';               File='numeral.min.js' },
    @{ Name='bignumber.js 11.1.5'; Url='https://cdn.jsdelivr.net/npm/bignumber.js@11.1.5/dist/bignumber.min.js';       File='bignumber.min.js' },
    @{ Name='accounting.js 0.4.1'; Url='https://cdn.jsdelivr.net/npm/accounting@0.4.1/accounting.min.js';             File='accounting.min.js' },
    @{ Name='plotly.js 3.7.0';     Url='https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.7.0/plotly.min.js';           File='plotly.min.js' }
)

Write-Host '============================================================'
Write-Host 'SST Math Lab v0.2.0 - dependency installer'
Write-Host '============================================================'

foreach ($Item in $Items) {
    $Out = Join-Path $Lib $Item.File
    if ((Test-Path $Out) -and ((Get-Item $Out).Length -gt 100)) {
        Write-Host ('[OK]  ' + $Item.Name)
        continue
    }
    Write-Host ('[GET] ' + $Item.Name)
    Invoke-WebRequest -UseBasicParsing -Uri $Item.Url -OutFile $Out
    if (-not (Test-Path $Out) -or (Get-Item $Out).Length -le 100) {
        throw "Downloaded file is missing or too small: $Out"
    }
}

Write-Host '[OK] All six libraries are available locally.'
