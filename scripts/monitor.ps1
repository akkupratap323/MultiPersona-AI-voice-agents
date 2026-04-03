# NesterVoiceAI Monitoring Script for PowerShell
# Monitor your deployment remotely from Windows

param(
    [string]$Command = "status",
    [string]$Service = "all"
)

# SSH Configuration - Update these paths for your system
$SSH_KEY = Join-Path $PSScriptRoot "LightsailDefaultKey-ap-south-1 (2).pem"
$SSH_USER = "ec2-user"
$SSH_HOST = "3.6.64.48"
$PROJECT_DIR = "nester-bot"

function Show-Help {
    Write-Host @"
NesterVoiceAI Monitoring Commands
==================================

Usage: .\monitor.ps1 -Command <command> [-Service <service>]

Commands:
  status          Show container status
  logs            Show logs (use -Service to specify which)
  health          Run health check
  restart         Restart containers
  stats           Show resource usage
  errors          Show recent errors
  full            Full diagnostic report

Services (for logs command):
  all, backend, frontend, caddy

Examples:
  .\monitor.ps1 -Command status
  .\monitor.ps1 -Command logs -Service backend
  .\monitor.ps1 -Command errors
  .\monitor.ps1 -Command restart
"@
}

function Invoke-SSHCommand {
    param([string]$Cmd)
    ssh -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "cd $PROJECT_DIR && $Cmd"
}

switch ($Command.ToLower()) {
    "status" {
        Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml ps"
    }

    "logs" {
        $lines = 50
        Write-Host "`n=== Logs ($Service) ===" -ForegroundColor Cyan

        if ($Service -eq "all") {
            Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=$lines"
        } else {
            Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=$lines $Service"
        }
    }

    "health" {
        Write-Host "`n=== Health Check ===" -ForegroundColor Cyan
        Invoke-SSHCommand "./monitor.sh"
    }

    "restart" {
        Write-Host "`n=== Restarting Containers ===" -ForegroundColor Yellow
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml restart"
        Write-Host "`nWaiting 10 seconds for services to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml ps"
    }

    "stats" {
        Write-Host "`n=== Resource Usage ===" -ForegroundColor Cyan
        Invoke-SSHCommand "docker stats --no-stream"
        Write-Host "`n=== System Memory ===" -ForegroundColor Cyan
        Invoke-SSHCommand "free -h"
    }

    "errors" {
        Write-Host "`n=== Recent Errors (Backend) ===" -ForegroundColor Red
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=100 backend | grep -i 'error\|exception\|failed'"

        Write-Host "`n=== Recent Warnings (Backend) ===" -ForegroundColor Yellow
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=100 backend | grep -i 'warning'"
    }

    "full" {
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "  NesterVoiceAI Full Diagnostic Report" -ForegroundColor Cyan
        Write-Host "========================================`n" -ForegroundColor Cyan

        Write-Host "1. Container Status:" -ForegroundColor Green
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml ps"

        Write-Host "`n2. Resource Usage:" -ForegroundColor Green
        Invoke-SSHCommand "docker stats --no-stream"

        Write-Host "`n3. System Resources:" -ForegroundColor Green
        Invoke-SSHCommand "free -h && echo '' && df -h /"

        Write-Host "`n4. Backend Health:" -ForegroundColor Green
        Invoke-SSHCommand "curl -s http://localhost:7860/health"

        Write-Host "`n5. Recent Backend Logs:" -ForegroundColor Green
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=20 backend"

        Write-Host "`n6. Recent Errors:" -ForegroundColor Green
        Invoke-SSHCommand "docker-compose -f docker-compose.https.yml logs --tail=100 backend | grep -i 'error' | tail -10"

        Write-Host "`n7. Container Restart Counts:" -ForegroundColor Green
        Invoke-SSHCommand "docker inspect nester-backend nester-frontend nester-caddy --format='{{.Name}}: {{.RestartCount}}' 2>/dev/null"

        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "  Report Complete" -ForegroundColor Cyan
        Write-Host "========================================`n" -ForegroundColor Cyan
    }

    "help" {
        Show-Help
    }

    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}
