#!/bin/bash

##############################################################################
# Quick Start Script for Kafka & ELK Stack Data Pipeline
# This script sets up and starts the entire data pipeline locally
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="data-pipeline-kafka"
REQUIRED_DOCKER_VERSION="20.10"
REQUIRED_COMPOSE_VERSION="2.0"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

##############################################################################
# Pre-flight Checks
##############################################################################

preflight_checks() {
    print_header "Running Pre-flight Checks"

    local all_checks_passed=true

    # Check Docker
    if check_command docker; then
        docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)
        print_info "Docker version: $docker_version"
    else
        print_error "Please install Docker: https://docs.docker.com/get-docker/"
        all_checks_passed=false
    fi

    # Check Docker Compose
    if check_command docker-compose || docker compose version &> /dev/null; then
        print_success "Docker Compose is available"
    else
        print_error "Please install Docker Compose"
        all_checks_passed=false
    fi

    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running. Please start Docker."
        all_checks_passed=false
    fi

    # Check available disk space (minimum 10GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -gt 10 ]; then
        print_success "Sufficient disk space available: ${available_space}GB"
    else
        print_warning "Low disk space: ${available_space}GB (recommended: 10GB+)"
    fi

    # Check available memory (minimum 4GB recommended)
    if command -v free &> /dev/null; then
        available_mem=$(free -g | awk 'NR==2 {print $7}')
        if [ "$available_mem" -gt 4 ]; then
            print_success "Sufficient memory available: ${available_mem}GB"
        else
            print_warning "Low available memory: ${available_mem}GB (recommended: 4GB+)"
        fi
    fi

    if [ "$all_checks_passed" = false ]; then
        print_error "Pre-flight checks failed. Please fix the issues above."
        exit 1
    fi

    print_success "All pre-flight checks passed!"
}

##############################################################################
# Environment Setup
##############################################################################

setup_environment() {
    print_header "Setting up Environment"

    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_info "Creating .env file from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "Please review and update .env file with your configurations"
    else
        print_info ".env file already exists"
    fi

    # Create required directories
    print_info "Creating required directories..."
    mkdir -p data/kafka
    mkdir -p data/zookeeper
    mkdir -p data/elasticsearch
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p logs
    mkdir -p reports

    print_success "Directories created"
}

##############################################################################
# Docker Operations
##############################################################################

start_infrastructure() {
    print_header "Starting Infrastructure Services"

    print_info "Starting Zookeeper and Kafka..."
    docker-compose up -d zookeeper kafka

    # Wait for Kafka to be ready
    print_info "Waiting for Kafka to be ready (this may take 30-60 seconds)..."
    sleep 30

    # Check Kafka health
    if docker-compose ps kafka | grep -q "Up"; then
        print_success "Kafka is running"
    else
        print_error "Kafka failed to start"
        docker-compose logs kafka
        exit 1
    fi

    print_success "Infrastructure services started"
}

start_elk_stack() {
    print_header "Starting ELK Stack"

    print_info "Starting Elasticsearch..."
    docker-compose up -d elasticsearch

    print_info "Waiting for Elasticsearch to be ready (this may take 30-60 seconds)..."
    sleep 30

    # Wait for Elasticsearch to be healthy
    max_retries=30
    retry_count=0
    while ! curl -s http://localhost:9200/_cluster/health &> /dev/null; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -gt $max_retries ]; then
            print_error "Elasticsearch failed to start within expected time"
            docker-compose logs elasticsearch
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Elasticsearch is running"

    print_info "Starting Logstash..."
    docker-compose up -d logstash
    sleep 10
    print_success "Logstash is running"

    print_info "Starting Kibana..."
    docker-compose up -d kibana

    print_info "Waiting for Kibana to be ready (this may take 30-60 seconds)..."
    sleep 30

    max_retries=30
    retry_count=0
    while ! curl -s http://localhost:5601/api/status &> /dev/null; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -gt $max_retries ]; then
            print_error "Kibana failed to start within expected time"
            docker-compose logs kibana
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Kibana is running"

    print_success "ELK Stack started successfully"
}

start_supporting_services() {
    print_header "Starting Supporting Services"

    print_info "Starting PostgreSQL, Redis, and Kafka UI..."
    docker-compose up -d postgres redis kafka-ui

    sleep 10
    print_success "Supporting services started"
}

start_data_pipeline() {
    print_header "Starting Data Pipeline Services"

    print_info "Starting producers..."
    docker-compose up -d log-producer metrics-producer

    sleep 5
    print_success "Producers started"

    print_info "Starting consumers..."
    docker-compose up -d elasticsearch-consumer

    sleep 5
    print_success "Consumers started"
}

start_monitoring() {
    print_header "Starting Monitoring Services"

    print_info "Starting Prometheus and Grafana..."
    docker-compose up -d prometheus grafana

    sleep 10
    print_success "Monitoring services started"
}

##############################################################################
# Health Checks
##############################################################################

check_service_health() {
    print_header "Checking Service Health"

    local all_healthy=true

    # Check Kafka
    if curl -s http://localhost:9092 &> /dev/null || docker-compose ps kafka | grep -q "Up"; then
        print_success "Kafka: Healthy"
    else
        print_error "Kafka: Unhealthy"
        all_healthy=false
    fi

    # Check Elasticsearch
    if curl -s http://localhost:9200/_cluster/health | grep -q "status"; then
        es_status=$(curl -s http://localhost:9200/_cluster/health | grep -oP '"status":"\K[^"]+')
        if [ "$es_status" = "green" ] || [ "$es_status" = "yellow" ]; then
            print_success "Elasticsearch: Healthy ($es_status)"
        else
            print_warning "Elasticsearch: Status is $es_status"
        fi
    else
        print_error "Elasticsearch: Unreachable"
        all_healthy=false
    fi

    # Check Kibana
    if curl -s http://localhost:5601/api/status &> /dev/null; then
        print_success "Kibana: Healthy"
    else
        print_error "Kibana: Unreachable"
        all_healthy=false
    fi

    # Check Logstash
    if curl -s http://localhost:9600/_node/stats &> /dev/null; then
        print_success "Logstash: Healthy"
    else
        print_warning "Logstash: May still be starting..."
    fi

    # Check Kafka UI
    if curl -s http://localhost:8080 &> /dev/null; then
        print_success "Kafka UI: Healthy"
    else
        print_warning "Kafka UI: May still be starting..."
    fi

    # Check Grafana
    if curl -s http://localhost:3001 &> /dev/null; then
        print_success "Grafana: Healthy"
    else
        print_warning "Grafana: May still be starting..."
    fi

    if [ "$all_healthy" = false ]; then
        print_warning "Some services are not healthy. Check logs with: docker-compose logs <service>"
    else
        print_success "All critical services are healthy!"
    fi
}

##############################################################################
# Display Information
##############################################################################

display_access_info() {
    print_header "Access Information"

    echo -e "${GREEN}🎉 Data Pipeline is Ready!${NC}\n"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Service URLs:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  📊 Kibana Dashboard:    ${GREEN}http://localhost:5601${NC}"
    echo -e "  🔍 Elasticsearch:       ${GREEN}http://localhost:9200${NC}"
    echo -e "  📈 Kafka UI:            ${GREEN}http://localhost:8080${NC}"
    echo -e "  📉 Grafana:             ${GREEN}http://localhost:3001${NC}"
    echo -e "     └─ Username: admin | Password: admin123"
    echo -e "  🔴 Prometheus:          ${GREEN}http://localhost:9090${NC}"
    echo -e "  🔌 API Gateway:         ${GREEN}http://localhost:3000${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}Quick Commands:${NC}"
    echo -e "  View all logs:          ${GREEN}docker-compose logs -f${NC}"
    echo -e "  View specific service:  ${GREEN}docker-compose logs -f <service>${NC}"
    echo -e "  Stop all services:      ${GREEN}docker-compose down${NC}"
    echo -e "  Restart service:        ${GREEN}docker-compose restart <service>${NC}"
    echo -e "  Check status:           ${GREEN}docker-compose ps${NC}\n"

    echo -e "${YELLOW}Useful Kibana Features:${NC}"
    echo -e "  1. Go to ${GREEN}http://localhost:5601${NC}"
    echo -e "  2. Click 'Discover' in the left menu"
    echo -e "  3. Create data view with pattern: ${GREEN}pipeline-logs-*${NC}"
    echo -e "  4. Start exploring your logs and metrics!\n"

    echo -e "${YELLOW}Sample Queries:${NC}"
    echo -e "  Elasticsearch health:   ${GREEN}curl http://localhost:9200/_cluster/health?pretty${NC}"
    echo -e "  List Kafka topics:      ${GREEN}docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092${NC}"
    echo -e "  Check log count:        ${GREEN}curl http://localhost:9200/pipeline-logs-*/_count?pretty${NC}\n"
}

##############################################################################
# Cleanup Functions
##############################################################################

cleanup() {
    print_header "Cleanup"

    read -p "Do you want to remove all data volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping and removing all containers and volumes..."
        docker-compose down -v
        print_success "All containers and volumes removed"

        print_info "Removing local data directories..."
        rm -rf data/kafka data/zookeeper data/elasticsearch data/postgres data/redis
        print_success "Local data directories removed"
    else
        print_info "Stopping containers only (keeping data)..."
        docker-compose down
        print_success "Containers stopped (data preserved)"
    fi
}

##############################################################################
# Main Function
##############################################################################

main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    Data Pipeline - Kafka & ELK Stack                     ║
    ║    Real-Time Monitoring & Logging System                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # Parse command line arguments
    case "${1:-start}" in
        start)
            preflight_checks
            setup_environment
            start_infrastructure
            start_elk_stack
            start_supporting_services
            start_data_pipeline
            start_monitoring

            print_info "Waiting for services to stabilize..."
            sleep 10

            check_service_health
            display_access_info
            ;;
        stop)
            print_header "Stopping All Services"
            docker-compose down
            print_success "All services stopped"
            ;;
        restart)
            print_header "Restarting All Services"
            docker-compose restart
            print_success "All services restarted"
            ;;
        cleanup)
            cleanup
            ;;
        logs)
            docker-compose logs -f
            ;;
        status)
            print_header "Service Status"
            docker-compose ps
            echo ""
            check_service_health
            ;;
        help|--help|-h)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start     - Start all services (default)"
            echo "  stop      - Stop all services"
            echo "  restart   - Restart all services"
            echo "  cleanup   - Stop and remove all containers and volumes"
            echo "  logs      - View logs from all services"
            echo "  status    - Check status of all services"
            echo "  help      - Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

##############################################################################
# Script Entry Point
##############################################################################

main "$@"
