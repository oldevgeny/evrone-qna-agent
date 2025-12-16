#!/usr/bin/env bash
set -euo pipefail

# QnA Agent Infrastructure Setup Script
# Deploys complete infrastructure: Hetzner Cloud + k3s + Application

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
        log_error "$1 is not installed. Please install it first."
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=0
    for cmd in terraform docker ssh ssh-keygen curl; do
        if ! check_command "$cmd"; then
            missing=1
        fi
    done

    if [[ $missing -eq 1 ]]; then
        log_error "Missing required tools. Please install them and try again."
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# Validate environment variables
validate_env() {
    log_info "Validating environment variables..."

    local missing=0

    if [[ -z "${HCLOUD_TOKEN:-}" ]]; then
        log_error "HCLOUD_TOKEN is required"
        missing=1
    fi

    if [[ -z "${DB_PASSWORD:-}" ]]; then
        log_error "DB_PASSWORD is required"
        missing=1
    fi

    if [[ -z "${LITELLM_API_KEY:-}" ]]; then
        log_error "LITELLM_API_KEY is required"
        missing=1
    fi

    if [[ $missing -eq 1 ]]; then
        echo ""
        log_error "Missing required environment variables."
        echo "Required:"
        echo "  export HCLOUD_TOKEN='your-hetzner-api-token'"
        echo "  export DB_PASSWORD='your-secure-database-password'"
        echo "  export LITELLM_API_KEY='your-openrouter-api-key'"
        echo ""
        echo "Optional:"
        echo "  export ADMIN_IP='your-ip/32'  # Auto-detected if not set"
        echo "  export DOMAIN='your-domain.com'"
        echo "  export ACME_EMAIL='your-email@example.com'"
        echo "  export LANGFUSE_PUBLIC_KEY='your-langfuse-public-key'"
        echo "  export LANGFUSE_SECRET_KEY='your-langfuse-secret-key'"
        exit 1
    fi

    # Auto-detect admin IP if not set (IPv4 only)
    if [[ -z "${ADMIN_IP:-}" ]]; then
        log_info "Auto-detecting admin IP (IPv4)..."
        # Try multiple services to get IPv4
        ADMIN_IP="$(curl -4 -s --max-time 5 https://api.ipify.org 2>/dev/null || \
                    curl -4 -s --max-time 5 https://ipv4.icanhazip.com 2>/dev/null || \
                    curl -4 -s --max-time 5 ifconfig.me 2>/dev/null || \
                    echo "")"

        # Validate it's an IPv4 address
        if [[ ! "$ADMIN_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            log_error "Could not detect IPv4 address. Please set ADMIN_IP manually."
            log_info "Example: export ADMIN_IP='1.2.3.4/32'"
            exit 1
        fi

        ADMIN_IP="$ADMIN_IP/32"
        log_info "Detected IP: $ADMIN_IP"
    fi

    log_success "Environment variables validated"
}

# Setup SSH key
setup_ssh_key() {
    log_info "Checking SSH key..."

    if [[ ! -f ~/.ssh/id_rsa.pub ]]; then
        log_warn "SSH key not found, generating new key..."
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -q
        log_success "SSH key generated"
    else
        log_success "SSH key found"
    fi
}

# Initialize Terraform
terraform_init() {
    log_info "Initializing Terraform..."
    terraform -chdir="$TERRAFORM_DIR" init -upgrade
    log_success "Terraform initialized"
}

# Apply Terraform - Hetzner module only
terraform_apply_hetzner() {
    log_info "Applying Terraform (Hetzner infrastructure)..."

    TF_VAR_hcloud_token="$HCLOUD_TOKEN" \
    TF_VAR_db_password="$DB_PASSWORD" \
    TF_VAR_litellm_api_key="$LITELLM_API_KEY" \
    TF_VAR_admin_ips="[\"$ADMIN_IP\"]" \
    TF_VAR_domain="${DOMAIN:-}" \
    TF_VAR_acme_email="${ACME_EMAIL:-}" \
    TF_VAR_langfuse_public_key="${LANGFUSE_PUBLIC_KEY:-}" \
    TF_VAR_langfuse_secret_key="${LANGFUSE_SECRET_KEY:-}" \
    terraform -chdir="$TERRAFORM_DIR" apply -target=module.hetzner -auto-approve

    log_success "Hetzner infrastructure created"
}

# Apply Terraform - Kubernetes module
terraform_apply_kubernetes() {
    log_info "Applying Terraform (Kubernetes resources)..."

    TF_VAR_hcloud_token="$HCLOUD_TOKEN" \
    TF_VAR_db_password="$DB_PASSWORD" \
    TF_VAR_litellm_api_key="$LITELLM_API_KEY" \
    TF_VAR_admin_ips="[\"$ADMIN_IP\"]" \
    TF_VAR_domain="${DOMAIN:-}" \
    TF_VAR_acme_email="${ACME_EMAIL:-}" \
    TF_VAR_langfuse_public_key="${LANGFUSE_PUBLIC_KEY:-}" \
    TF_VAR_langfuse_secret_key="${LANGFUSE_SECRET_KEY:-}" \
    terraform -chdir="$TERRAFORM_DIR" apply -auto-approve

    log_success "Kubernetes resources created"
}

# Get server IP from Terraform output
get_server_ip() {
    terraform -chdir="$TERRAFORM_DIR" output -raw server_ip
}

# Wait for k3s to be ready
wait_for_k3s() {
    local server_ip=$1
    local max_attempts=60
    local attempt=1

    log_info "Waiting for k3s to be ready (this may take 3-5 minutes)..."

    while [[ $attempt -le $max_attempts ]]; do
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "root@$server_ip" "kubectl get nodes" &>/dev/null; then
            log_success "k3s is ready"
            return 0
        fi
        echo -n "."
        sleep 10
        ((attempt++))
    done

    echo ""
    log_error "Timeout waiting for k3s to be ready"
    return 1
}

# Fetch kubeconfig
fetch_kubeconfig() {
    local server_ip=$1

    log_info "Fetching kubeconfig..."

    mkdir -p ~/.kube
    scp -o StrictHostKeyChecking=no "root@$server_ip:/etc/rancher/k3s/k3s.yaml" ~/.kube/config

    # Update server address in kubeconfig
    sed -i.bak "s/127.0.0.1/$server_ip/g" ~/.kube/config
    rm -f ~/.kube/config.bak

    log_success "Kubeconfig configured"
}

# Wait for Traefik CRDs to be available
wait_for_traefik_crds() {
    log_info "Waiting for Traefik CRDs to be installed..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if kubectl get crd ingressroutes.traefik.io &>/dev/null; then
            log_success "Traefik CRDs are ready"
            return 0
        fi
        echo -n "."
        sleep 10
        ((attempt++))
    done

    echo ""
    log_error "Timeout waiting for Traefik CRDs"
    return 1
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    docker build -t qna-agent:latest "$PROJECT_ROOT"
    log_success "Docker image built"
}

# Push image to k3s server
push_image_to_k3s() {
    local server_ip=$1

    log_info "Pushing Docker image to k3s server..."

    # Save image to tarball
    docker save qna-agent:latest | gzip > /tmp/qna-agent.tar.gz

    # Copy to server
    scp -o StrictHostKeyChecking=no /tmp/qna-agent.tar.gz "root@$server_ip:/tmp/"

    # Import into k3s
    ssh -o StrictHostKeyChecking=no "root@$server_ip" "k3s ctr images import /tmp/qna-agent.tar.gz"

    # Cleanup
    rm -f /tmp/qna-agent.tar.gz
    ssh -o StrictHostKeyChecking=no "root@$server_ip" "rm -f /tmp/qna-agent.tar.gz"

    log_success "Docker image pushed to k3s"
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        local ready=$(kubectl -n qna-agent get deployment qna-agent -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired=$(kubectl -n qna-agent get deployment qna-agent -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "2")

        if [[ "$ready" == "$desired" && "$ready" != "0" ]]; then
            log_success "Deployment is ready ($ready/$desired replicas)"
            return 0
        fi

        echo -n "."
        sleep 10
        ((attempt++))
    done

    echo ""
    log_warn "Deployment may not be fully ready. Check with: kubectl -n qna-agent get pods"
    return 0
}

# Health check
health_check() {
    local server_ip=$1

    log_info "Running health check..."

    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://$server_ip/health/live" | grep -q "200"; then
            log_success "Health check passed"
            return 0
        fi
        sleep 5
        ((attempt++))
    done

    log_warn "Health check did not pass. The application may still be starting."
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
    echo "Server IP: $server_ip"
    echo ""
    echo "Access URLs:"
    echo "  API:     http://$server_ip"
    echo "  Health:  http://$server_ip/health/live"
    echo "  Docs:    http://$server_ip/docs"

    if [[ -n "${DOMAIN:-}" ]]; then
        echo "  Domain:  https://$DOMAIN"
    fi

    echo ""
    echo "Useful commands:"
    echo "  kubectl -n qna-agent get pods       # Check pod status"
    echo "  kubectl -n qna-agent logs -f -l app=qna-agent  # View logs"
    echo "  make k8s-status                     # Check all resources"
    echo "  make infra-destroy                  # Tear down infrastructure"
    echo ""
}

# Main function
main() {
    echo ""
    echo "=============================================="
    echo "QnA Agent Infrastructure Setup"
    echo "=============================================="
    echo ""

    check_prerequisites
    validate_env
    setup_ssh_key
    terraform_init

    # Stage 1: Create Hetzner infrastructure
    terraform_apply_hetzner

    local server_ip
    server_ip=$(get_server_ip)

    # Stage 2: Wait for k3s and configure kubectl
    wait_for_k3s "$server_ip"
    fetch_kubeconfig "$server_ip"

    # Stage 3: Wait for Traefik CRDs (installed via Helm in user_data)
    wait_for_traefik_crds

    # Stage 4: Build and push Docker image
    build_docker_image
    push_image_to_k3s "$server_ip"

    # Stage 5: Apply Kubernetes resources via Terraform
    terraform_apply_kubernetes

    # Stage 5: Verify deployment
    wait_for_deployment
    health_check "$server_ip"
    print_summary "$server_ip"
}

# Run main
main "$@"
