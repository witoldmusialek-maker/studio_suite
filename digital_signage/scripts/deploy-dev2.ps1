param(
  [string]$DevHost = "dev1",
  [string]$RemoteRepoRoot = "~/projects/projekt2_repo",
  [string]$Branch = "master"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

Write-Host "[1/3] Pull + deploy projekt2 na dev1 ($Branch)..."
Run-Native "ssh $DevHost `"cd $RemoteRepoRoot && git fetch origin && git checkout $Branch && git pull origin $Branch && cd digital_signage && docker compose up -d --build && docker compose ps`""

Write-Host "[2/3] Smoke test publicznego URL (dev2)..."
& "$PSScriptRoot\smoke-test.ps1" -BaseUrl "https://dev2.witold.ovh"

Write-Host "[3/3] DONE: deploy + smoke zakoñczone."