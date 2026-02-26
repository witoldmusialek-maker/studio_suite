param(
  [string]$BaseUrl = "https://dev2.witold.ovh"
)

$ErrorActionPreference = "Stop"

function Get-StatusCode([string]$Url, [string]$Method = "GET") {
  $code = curl.exe -s -o NUL -w "%{http_code}" -X $Method $Url
  return [int]$code
}

function Assert-Status([string]$Url, [int]$Expected, [string]$Method = "GET") {
  $got = Get-StatusCode -Url $Url -Method $Method
  if ($got -ne $Expected) {
    throw "FAIL $Method $Url -> $got (expected $Expected)"
  }
  Write-Host "OK   $Method $Url -> $got"
}

Write-Host "Smoke test: $BaseUrl"
Assert-Status "$BaseUrl/" 200
Assert-Status "$BaseUrl/health" 200
Assert-Status "$BaseUrl/api/v1/auth/login" 405 "GET"

Write-Host "DONE: smoke test przeszed³."
