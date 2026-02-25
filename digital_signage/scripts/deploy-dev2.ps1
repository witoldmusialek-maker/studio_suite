param(
  [string]$DevHost = "dev1",
  [string]$RemoteRepoRoot = "~/projects/projekt2_repo",
  [string]$Branch = "master",
  [string]$PublicBaseUrl = "https://dev2.witold.ovh",
  [string]$DirectApiBaseUrl = "http://192.168.200.116:8003",
  [switch]$SkipPublicSmoke
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

Write-Host "[1/4] Pull + deploy projekt2 na dev1 ($Branch)..."
Run-Native "ssh $DevHost `"cd $RemoteRepoRoot && git fetch origin && git checkout $Branch && git pull origin $Branch && cd digital_signage && docker compose up -d --build && docker compose ps`""

Write-Host "[2/4] Smoke test direct (dev1:8003)..."
& "$PSScriptRoot\smoke-test.ps1" -BaseUrl $DirectApiBaseUrl

if (-not $SkipPublicSmoke) {
  Write-Host "[3/4] Smoke test publicznego URL (dev2)..."
  & "$PSScriptRoot\smoke-test.ps1" -BaseUrl $PublicBaseUrl
} else {
  Write-Host "[3/4] Pomijam smoke publicznego URL (SkipPublicSmoke)." -ForegroundColor Yellow
}

Write-Host "[4/4] DONE: deploy + smoke zakonczone."