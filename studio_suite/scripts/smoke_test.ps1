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

$displayId = $null
$groupId = $null

try {
    Step "Checking health endpoint"
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Ensure ($health.status -eq "ok") "Health check failed"

    Step "Logging in as $Username"
    $loginBody = @{
        username = $Username
        password = $Password
    } | ConvertTo-Json
    $tokenResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
    Ensure (-not [string]::IsNullOrWhiteSpace($tokenResponse.access_token)) "Login did not return access_token"

    $headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }

    Step "Validating auth/me"
    $me = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -Method Get -Headers $headers
    Ensure ($me.username -eq $Username) "auth/me returned unexpected username"

    $suffix = Get-Random -Minimum 10000 -Maximum 99999
    $mac = "02:00:00:00:$($suffix.ToString().Substring(0,2)):$($suffix.ToString().Substring(2,3).PadLeft(2,'0').Substring(0,2))"

    Step "Creating display"
    $displayBody = @{
        name = "smoke-display-$suffix"
        mac_address = $mac
        orientation = 0
        resolution_width = 1920
        resolution_height = 1080
        floor = "smoke"
        position_x = 0
        position_y = 0
        cache_size_mb = 256
    } | ConvertTo-Json
    $display = Invoke-RestMethod -Uri "$BaseUrl/api/v1/displays/" -Method Post -Headers $headers -ContentType "application/json" -Body $displayBody
    $displayId = $display.id
    Ensure ($displayId -gt 0) "Display was not created"

    Step "Sending heartbeat"
    $heartbeatBody = @{ current_content_id = $null; cache_status = @{}; errors = @() } | ConvertTo-Json
    $heartbeat = Invoke-RestMethod -Uri "$BaseUrl/api/v1/displays/$displayId/heartbeat" -Method Post -ContentType "application/json" -Body $heartbeatBody
    Ensure ($heartbeat.status -eq "ok") "Heartbeat failed"

    Step "Creating group and assigning display"
    $groupBody = @{
        name = "smoke-group-$suffix"
        type = "horizontal"
        floor = "smoke"
        layout_config = @{}
    } | ConvertTo-Json
    $group = Invoke-RestMethod -Uri "$BaseUrl/api/v1/groups/" -Method Post -Headers $headers -ContentType "application/json" -Body $groupBody
    $groupId = $group.id
    Ensure ($groupId -gt 0) "Group was not created"

    $addResult = Invoke-RestMethod -Uri "$BaseUrl/api/v1/groups/$groupId/displays/$displayId" -Method Post -Headers $headers
    Ensure ($addResult.message -eq "Display added to group") "Display was not added to group"

    Step "Checking reports endpoints"
    $daily = Invoke-RestMethod -Uri "$BaseUrl/api/v1/reports/daily" -Method Get -Headers $headers
    Ensure ($null -ne $daily.displays) "Daily report does not contain displays"

    $weekly = Invoke-RestMethod -Uri "$BaseUrl/api/v1/reports/weekly" -Method Get -Headers $headers
    Ensure ($null -ne $weekly.displays) "Weekly report does not contain displays"

    $today = (Get-Date).ToString("yyyy-MM-dd")
    $offline = Invoke-RestMethod -Uri "$BaseUrl/api/v1/reports/offline?display_id=$displayId&start_date=$today&end_date=$today" -Method Get -Headers $headers
    Ensure ($offline.display_id -eq $displayId) "Offline report returned unexpected display"

    Step "Smoke test passed"
    Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
}
finally {
    Step "Cleanup"
    if ($groupId) {
        try {
            if ($displayId) {
                Invoke-RestMethod -Uri "$BaseUrl/api/v1/groups/$groupId/displays/$displayId" -Method Delete -Headers $headers | Out-Null
            }
        }
        catch {
            Write-Warning "Failed to remove display from group: $($_.Exception.Message)"
        }

        try {
            Invoke-RestMethod -Uri "$BaseUrl/api/v1/groups/$groupId" -Method Delete -Headers $headers | Out-Null
        }
        catch {
            Write-Warning "Failed to delete group ${groupId}: $($_.Exception.Message)"
        }
    }

    if ($displayId) {
        try {
            Invoke-RestMethod -Uri "$BaseUrl/api/v1/displays/$displayId" -Method Delete -Headers $headers | Out-Null
        }
        catch {
            Write-Warning "Failed to delete display ${displayId}: $($_.Exception.Message)"
        }
    }
}
