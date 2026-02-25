param(
  [string]$DevHost = "dev1",
  [string]$NginxSite = "/etc/nginx/sites-available/dev2.witold.ovh",
  [string]$NginxEnabledLink = "/etc/nginx/sites-enabled/dev2.witold.ovh"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

$localConf = Join-Path $PSScriptRoot "..\nginx\dev2.witold.ovh.conf"
if (!(Test-Path $localConf)) { throw "Missing nginx conf: $localConf" }

Write-Host "[1/4] Upload nginx config..."
Run-Native "scp `"$localConf`" $DevHost`:~/dev2.witold.ovh.conf"

Write-Host "[2/4] Install config + enable site..."
Run-Native "ssh $DevHost `"sudo mv ~/dev2.witold.ovh.conf $NginxSite && sudo ln -sf $NginxSite $NginxEnabledLink`""

Write-Host "[3/4] Validate nginx config..."
Run-Native "ssh $DevHost `"sudo nginx -t`""

Write-Host "[4/4] Reload nginx..."
Run-Native "ssh $DevHost `"sudo systemctl reload nginx`""

Write-Host "DONE: nginx vhost for dev2.witold.ovh is enabled."