# Quick Commands for NesterVoiceAI
# Easy shortcuts for common operations

$SSH_KEY = Join-Path $PSScriptRoot "LightsailDefaultKey-ap-south-1 (2).pem"
$SSH_USER = "ec2-user"
$SSH_HOST = "3.6.64.48"
$PROJECT_DIR = "nester-bot"

function SSH-Run {
    param([string]$Cmd)
    ssh -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "cd $PROJECT_DIR && $Cmd"
}

# Quick command functions
function Show-Status {
    Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml ps"
}

function Show-BackendLogs {
    param([int]$Lines = 50)
    Write-Host "`n=== Backend Logs (last $Lines lines) ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml logs --tail=$Lines backend"
}

function Show-FrontendLogs {
    param([int]$Lines = 50)
    Write-Host "`n=== Frontend Logs (last $Lines lines) ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml logs --tail=$Lines frontend"
}

function Show-CaddyLogs {
    param([int]$Lines = 50)
    Write-Host "`n=== Caddy Logs (last $Lines lines) ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml logs --tail=$Lines caddy"
}

function Show-AllLogs {
    param([int]$Lines = 30)
    Write-Host "`n=== All Logs (last $Lines lines each) ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml logs --tail=$Lines"
}

function Follow-BackendLogs {
    Write-Host "`n=== Following Backend Logs (Ctrl+C to stop) ===" -ForegroundColor Cyan
    SSH-Run "docker-compose -f docker-compose.https.yml logs -f backend"
}

function Show-Errors {
    Write-Host "`n=== Recent Errors ===" -ForegroundColor Red
    SSH-Run "docker-compose -f docker-compose.https.yml logs --tail=200 | grep -i 'error\|exception\|failed' | tail -20"
}

function Restart-All {
    Write-Host "`n=== Restarting All Containers ===" -ForegroundColor Yellow
    SSH-Run "docker-compose -f docker-compose.https.yml restart"
    Write-Host "Waiting 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Show-Status
}

function Restart-Backend {
    Write-Host "`n=== Restarting Backend ===" -ForegroundColor Yellow
    SSH-Run "docker-compose -f docker-compose.https.yml restart backend"
    Write-Host "Waiting 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Show-Status
}

function Show-Stats {
    Write-Host "`n=== Resource Usage ===" -ForegroundColor Cyan
    SSH-Run "docker stats --no-stream"
}

function Show-Memory {
    Write-Host "`n=== System Memory ===" -ForegroundColor Cyan
    SSH-Run "free -h"
}

function Check-Health {
    Write-Host "`n=== Health Check ===" -ForegroundColor Cyan
    SSH-Run "curl -s http://localhost:7860/health | jq . || curl -s http://localhost:7860/health"
}

function Show-Menu {
    Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║         NesterVoiceAI Quick Commands                      ║
╚═══════════════════════════════════════════════════════════╝

LOGS:
  Show-BackendLogs [Lines]      Show backend logs
  Show-FrontendLogs [Lines]     Show frontend logs
  Show-CaddyLogs [Lines]        Show Caddy proxy logs
  Show-AllLogs [Lines]          Show all logs
  Follow-BackendLogs            Follow backend logs live
  Show-Errors                   Show recent errors only

STATUS:
  Show-Status                   Container status
  Show-Stats                    Resource usage
  Show-Memory                   System memory
  Check-Health                  Backend health check

CONTROL:
  Restart-All                   Restart all containers
  Restart-Backend               Restart backend only

HELP:
  Show-Menu                     Show this menu

EXAMPLES:
  Show-BackendLogs 100          Show last 100 backend logs
  Follow-BackendLogs            Watch backend logs in real-time
  Show-Errors                   See what's failing
  Restart-Backend               Quick backend restart

"@
}

# Show menu on load
Show-Menu
