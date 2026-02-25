param(
  [string]$GatewayHost = "gateway",
  [string]$GatewayConfDir = "/home/witold/gateway-services/nginx/conf.d",
  [string]$GatewayComposeDir = "/home/witold/gateway-services"
)

& "$PSScriptRoot\setup-gateway-dev2-nginx.ps1" -GatewayHost $GatewayHost -GatewayConfDir $GatewayConfDir -GatewayComposeDir $GatewayComposeDir