#!/bin/bash
# NesterVoiceAI Monitoring Script for macOS
# Quick commands to monitor your deployment from Mac Terminal

# SSH Configuration
SSH_KEY="LightsailDefaultKey-ap-south-1 (2).pem"
SSH_USER="ec2-user"
SSH_HOST="3.6.64.48"
PROJECT_DIR="nester-bot"

# Color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# SSH command wrapper
ssh_run() {
    ssh -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "cd $PROJECT_DIR && $1"
}

# Display help menu
show_help() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         NesterVoiceAI Monitoring Commands (macOS)        ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC} ./monitor-mac.sh [command] [options]"
    echo ""
    echo -e "${GREEN}LOGS:${NC}"
    echo "  logs                      Show all container logs (last 50 lines)"
    echo "  logs backend [N]          Show backend logs (last N lines, default 50)"
    echo "  logs frontend [N]         Show frontend logs"
    echo "  logs caddy [N]            Show Caddy proxy logs"
    echo "  follow                    Follow backend logs in real-time (Ctrl+C to stop)"
    echo "  errors                    Show recent errors only"
    echo ""
    echo -e "${GREEN}STATUS:${NC}"
    echo "  status                    Show container status"
    echo "  stats                     Show CPU/Memory usage"
    echo "  memory                    Show system memory"
    echo "  health                    Backend health check"
    echo ""
    echo -e "${GREEN}CONTROL:${NC}"
    echo "  restart                   Restart all containers"
    echo "  restart backend           Restart backend only"
    echo "  restart frontend          Restart frontend only"
    echo "  restart caddy             Restart Caddy only"
    echo ""
    echo -e "${GREEN}DIAGNOSTICS:${NC}"
    echo "  full                      Full diagnostic report"
    echo "  help                      Show this help menu"
    echo ""
    echo -e "${GREEN}EXAMPLES:${NC}"
    echo "  ./monitor-mac.sh status"
    echo "  ./monitor-mac.sh logs backend 100"
    echo "  ./monitor-mac.sh follow"
    echo "  ./monitor-mac.sh errors"
    echo "  ./monitor-mac.sh restart backend"
    echo ""
}

# Container status
show_status() {
    echo -e "\n${CYAN}=== Container Status ===${NC}"
    ssh_run "docker-compose -f docker-compose.https.yml ps"
}

# Show logs
show_logs() {
    local service="${1:-all}"
    local lines="${2:-50}"

    echo -e "\n${CYAN}=== Logs ($service - last $lines lines) ===${NC}"

    if [ "$service" = "all" ]; then
        ssh_run "docker-compose -f docker-compose.https.yml logs --tail=$lines"
    else
        ssh_run "docker-compose -f docker-compose.https.yml logs --tail=$lines $service"
    fi
}

# Follow logs in real-time
follow_logs() {
    local service="${1:-backend}"
    echo -e "\n${CYAN}=== Following $service Logs (Press Ctrl+C to stop) ===${NC}\n"
    ssh_run "docker-compose -f docker-compose.https.yml logs -f $service"
}

# Show errors
show_errors() {
    echo -e "\n${RED}=== Recent Errors ===${NC}"
    ssh_run "docker-compose -f docker-compose.https.yml logs --tail=200 | grep -i 'error\|exception\|failed' | tail -20"
}

# Resource usage
show_stats() {
    echo -e "\n${CYAN}=== Resource Usage ===${NC}"
    ssh_run "docker stats --no-stream"
}

# System memory
show_memory() {
    echo -e "\n${CYAN}=== System Memory ===${NC}"
    ssh_run "free -h"
}

# Health check
check_health() {
    echo -e "\n${CYAN}=== Health Check ===${NC}"
    ssh_run "curl -s http://localhost:7860/health | jq . 2>/dev/null || curl -s http://localhost:7860/health"
}

# Restart containers
restart_containers() {
    local service="${1:-}"

    if [ -z "$service" ]; then
        echo -e "\n${YELLOW}=== Restarting All Containers ===${NC}"
        ssh_run "docker-compose -f docker-compose.https.yml restart"
    else
        echo -e "\n${YELLOW}=== Restarting $service ===${NC}"
        ssh_run "docker-compose -f docker-compose.https.yml restart $service"
    fi

    echo -e "${YELLOW}Waiting 10 seconds for services to start...${NC}"
    sleep 10
    show_status
}

# Full diagnostic report
full_diagnostic() {
    echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  NesterVoiceAI Full Diagnostic Report${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

    echo -e "${GREEN}1. Container Status:${NC}"
    ssh_run "docker-compose -f docker-compose.https.yml ps"

    echo -e "\n${GREEN}2. Resource Usage:${NC}"
    ssh_run "docker stats --no-stream"

    echo -e "\n${GREEN}3. System Resources:${NC}"
    ssh_run "free -h && echo '' && df -h /"

    echo -e "\n${GREEN}4. Backend Health:${NC}"
    ssh_run "curl -s http://localhost:7860/health"

    echo -e "\n${GREEN}5. Recent Backend Logs:${NC}"
    ssh_run "docker-compose -f docker-compose.https.yml logs --tail=20 backend"

    echo -e "\n${GREEN}6. Recent Errors:${NC}"
    ssh_run "docker-compose -f docker-compose.https.yml logs --tail=100 backend | grep -i 'error' | tail -10"

    echo -e "\n${GREEN}7. Container Restart Counts:${NC}"
    ssh_run "docker inspect nester-backend nester-frontend nester-caddy --format='{{.Name}}: {{.RestartCount}}' 2>/dev/null"

    echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Report Complete${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"
}

# Main script logic
case "${1:-help}" in
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-all}" "${3:-50}"
        ;;
    follow)
        follow_logs "${2:-backend}"
        ;;
    errors)
        show_errors
        ;;
    stats)
        show_stats
        ;;
    memory)
        show_memory
        ;;
    health)
        check_health
        ;;
    restart)
        restart_containers "$2"
        ;;
    full)
        full_diagnostic
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        ;;
esac
