#!/usr/bin/env bash
set -euo pipefail

# QnA Agent Application Deployment Script
# Deploys/updates the application without recreating infrastructure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed."
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    for cmd in docker kubectl ssh; do
        check_command "$cmd" || exit 1
    done

    # Check if kubectl is configured
    if ! kubectl cluster-info &>/dev/null; then
        log_error "kubectl is not configured or cluster is not accessible"
        log_info "Run 'make infra-apply' first to set up the infrastructure"
        exit 1
    fi

    log_success "Prerequisites satisfied"
}

# Get server IP from kubeconfig or terraform
get_server_ip() {
    # Try to get from kubeconfig
    local server_url
    server_url=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null || echo "")

    if [[ -n "$server_url" ]]; then
        # Extract IP from URL like https://1.2.3.4:6443
        echo "$server_url" | sed -E 's|https?://([^:]+).*|\1|'
    elif [[ -f "$TERRAFORM_DIR/terraform.tfstate" ]]; then
        # Fallback to terraform output
        terraform -chdir="$TERRAFORM_DIR" output -raw server_ip 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Build Docker image
build_docker_image() {
    local tag="${1:-latest}"

    log_info "Building Docker image (tag: $tag)..."
    docker build -t "qna-agent:$tag" "$PROJECT_ROOT"
    log_success "Docker image built"
}

# Push image to k3s server
push_image_to_k3s() {
    local server_ip=$1
    local tag="${2:-latest}"

    log_info "Pushing Docker image to k3s server..."

    # Save image to tarball
    docker save "qna-agent:$tag" | gzip > /tmp/qna-agent.tar.gz

    # Copy to server
    scp -o StrictHostKeyChecking=no /tmp/qna-agent.tar.gz "root@$server_ip:/tmp/"

    # Import into k3s
    ssh -o StrictHostKeyChecking=no "root@$server_ip" "k3s ctr images import /tmp/qna-agent.tar.gz"

    # Cleanup
    rm -f /tmp/qna-agent.tar.gz
    ssh -o StrictHostKeyChecking=no "root@$server_ip" "rm -f /tmp/qna-agent.tar.gz"

    log_success "Docker image pushed to k3s"
}

# Restart deployment to pick up new image
restart_deployment() {
    log_info "Restarting deployment..."

    kubectl -n qna-agent rollout restart deployment/qna-agent

    log_success "Deployment restart initiated"
}

# Wait for rollout to complete
wait_for_rollout() {
    log_info "Waiting for rollout to complete..."

    if kubectl -n qna-agent rollout status deployment/qna-agent --timeout=300s; then
        log_success "Rollout complete"
    else
        log_error "Rollout failed or timed out"
        kubectl -n qna-agent get pods
        exit 1
    fi
}

# Health check
health_check() {
    local server_ip=$1

    log_info "Running health check..."

    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" "http://$server_ip/health/live" || echo "000")

        if [[ "$status" == "200" ]]; then
            log_success "Health check passed"
            return 0
        fi

        log_info "Waiting for health check (attempt $attempt/$max_attempts, status: $status)..."
        sleep 5
        ((attempt++))
    done

    log_warn "Health check did not pass. Check application logs."
    return 0
}

# Print summary
print_summary() {
    local server_ip=$1

    echo ""
    echo "=============================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "Application URL: http://$server_ip"
    echo ""
    echo "Useful commands:"
    echo "  kubectl -n qna-agent get pods"
    echo "  kubectl -n qna-agent logs -f -l app=qna-agent"
    echo ""
}

# Main function
main() {
    local tag="${1:-latest}"

    echo ""
    echo "=============================================="
    echo "QnA Agent Application Deployment"
    echo "=============================================="
    echo ""

    check_prerequisites

    local server_ip
    server_ip=$(get_server_ip)

    if [[ -z "$server_ip" ]]; then
        log_error "Could not determine server IP"
        log_info "Make sure infrastructure is deployed and kubeconfig is configured"
        exit 1
    fi

    log_info "Server IP: $server_ip"

    build_docker_image "$tag"
    push_image_to_k3s "$server_ip" "$tag"
    restart_deployment
    wait_for_rollout
    health_check "$server_ip"
    print_summary "$server_ip"
}

# Run main
main "$@"
