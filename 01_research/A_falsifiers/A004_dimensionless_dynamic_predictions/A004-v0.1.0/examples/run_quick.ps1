$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
python "$Root/src/sst_dimensionless_ratios.py" campaign `
  --config "$Root/configs/quick_campaign.json" `
  --output "$Root/outputs/quick_start"
