param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = $env:STUDIO_SUITE_SMOKE_USERNAME,
    [string]$Password = $env:STUDIO_SUITE_SMOKE_PASSWORD,
    [switch]$HealthOnly
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

if ($HealthOnly) {
    Write-Host "SMOKE HEALTH PASSED" -ForegroundColor Green
    return
}

if ([string]::IsNullOrWhiteSpace($Username) -or [string]::IsNullOrWhiteSpace($Password)) {
    throw "Authenticated smoke requires credentials. Set STUDIO_SUITE_SMOKE_USERNAME/STUDIO_SUITE_SMOKE_PASSWORD or pass -Username/-Password. Use -HealthOnly for non-secret runtime health. If the account requires TOTP, use a smoke account without TOTP or update this script with an approved TOTP flow."
}

Step "Logging in as $Username"
$loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json
try {
    $tokenResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
} catch {
    throw "Login failed. Check smoke credentials and TOTP requirements. Original error: $($_.Exception.Message)"
}
Ensure (-not [string]::IsNullOrWhiteSpace($tokenResponse.access_token)) "Login did not return access_token; account may require TOTP or credentials may be invalid"
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

Step "Checking booking/bootstrap"
$bootstrap = Invoke-RestMethod -Uri "$BaseUrl/api/v1/booking/bootstrap" -Method Get -Headers $headers
Ensure ($null -ne $bootstrap) "booking/bootstrap returned null"

Step "Checking legacy/reports/summary"
$summary = Invoke-RestMethod -Uri "$BaseUrl/api/v1/legacy/reports/summary" -Method Get -Headers $headers
Ensure ($null -ne $summary) "legacy/reports/summary returned null"

Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
