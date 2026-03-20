param(
  [string]$GatewayHost = "gateway",
  [string]$GatewayConfDir = "/home/witold/gateway-services/nginx/conf.d",
  [string]$GatewayComposeDir = "/home/witold/gateway-services"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

$localConf = Join-Path $PSScriptRoot "..\nginx\gateway-dev3.witold.ovh.conf"
if (!(Test-Path $localConf)) { throw "Missing gateway config: $localConf" }

Write-Host "[1/4] Upload gateway nginx config..."
Run-Native "scp `"$localConf`" $GatewayHost`:~/dev3.witold.ovh.conf"

Write-Host "[2/4] Install config in gateway-services..."
Run-Native "ssh $GatewayHost `"cp ~/dev3.witold.ovh.conf $GatewayConfDir/dev3.witold.ovh.conf`""

Write-Host "[3/4] Validate nginx config inside gateway nginx container..."
Run-Native "ssh $GatewayHost `"cd $GatewayComposeDir && docker compose exec -T nginx nginx -t`""

Write-Host "[4/4] Reload gateway nginx..."
Run-Native "ssh $GatewayHost `"cd $GatewayComposeDir && docker compose exec -T nginx nginx -s reload`""

Write-Host "DONE: gateway routing for dev3.witold.ovh is active."

