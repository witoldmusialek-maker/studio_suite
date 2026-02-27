param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Username = "admin",
    [string]$Password = "password123"
)

$scriptPath = Join-Path $PSScriptRoot 'smoke-test.ps1'
& $scriptPath -BaseUrl $BaseUrl -Username $Username -Password $Password
