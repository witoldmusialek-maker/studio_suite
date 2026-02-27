param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "admin",
    [string]$Password = "password123"
)

$ErrorActionPreference = "Stop"

function Step([string]$Message) {
    Write-Host "[SMOKE] $Message" -ForegroundColor Cyan
}

function Ensure([bool]$Condition, [string]$Message) {
    if (-not $Condition) {
        throw $Message
    }
}

Step "Checking health endpoint"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
Ensure ($health.status -eq "ok") "Health check failed"

Step "Logging in as $Username"
$loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json
$tokenResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
Ensure (-not [string]::IsNullOrWhiteSpace($tokenResponse.access_token)) "Login did not return access_token"
$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }

Step "Validating auth/me"
$me = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -Method Get -Headers $headers
Ensure ($me.username -eq $Username) "auth/me returned unexpected username"

Step "Checking resources/salons"
$salons = Invoke-RestMethod -Uri "$BaseUrl/api/v1/resources/salons" -Method Get -Headers $headers
Ensure ($null -ne $salons) "resources/salons returned null"

$salonId = $null
if ($salons.Count -gt 0) {
    $salonId = $salons[0].id
}

if ($null -ne $salonId) {
    Step "Checking legacy/catalog for salon_id=$salonId"
    $catalog = Invoke-RestMethod -Uri "$BaseUrl/api/v1/legacy/catalog?salon_id=$salonId" -Method Get -Headers $headers
    Ensure ($null -ne $catalog) "legacy/catalog returned null"
}

Step "Checking legacy/reports/summary"
$summary = Invoke-RestMethod -Uri "$BaseUrl/api/v1/legacy/reports/summary" -Method Get -Headers $headers
Ensure ($null -ne $summary) "legacy/reports/summary returned null"

Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
