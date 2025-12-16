#!/usr/bin/env bash
set -euo pipefail

# QnA Agent Infrastructure Teardown Script
# Destroys all infrastructure resources

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

# Validate environment
validate_env() {
    log_info "Validating environment..."

    if [[ -z "${HCLOUD_TOKEN:-}" ]]; then
        log_error "HCLOUD_TOKEN is required for teardown"
        echo "  export HCLOUD_TOKEN='your-hetzner-api-token'"
        exit 1
    fi

    log_success "Environment validated"
}

# Terraform destroy
terraform_destroy() {
    log_info "Destroying Terraform resources..."

    # Use dummy values for required variables during destroy
    TF_VAR_hcloud_token="$HCLOUD_TOKEN" \
    TF_VAR_db_password="dummy" \
    TF_VAR_litellm_api_key="" \
    TF_VAR_admin_ips='["0.0.0.0/0"]' \
    terraform -chdir="$TERRAFORM_DIR" destroy -auto-approve

    log_success "Terraform resources destroyed"
}

# Clean up local kubeconfig
cleanup_kubeconfig() {
    log_info "Cleaning up local kubeconfig..."

    if [[ -f ~/.kube/config ]]; then
        # Check if it's the k3s config we created
        if grep -q "k3s" ~/.kube/config 2>/dev/null; then
            rm -f ~/.kube/config
            log_success "Kubeconfig removed"
        else
            log_warn "Kubeconfig appears to be for a different cluster, skipping removal"
        fi
    else
        log_info "No kubeconfig found"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}Teardown Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "All infrastructure resources have been destroyed."
    echo ""
    echo "To redeploy:"
    echo "  make infra-apply"
    echo ""
}

# Main function
main() {
    echo ""
    echo "=============================================="
    echo -e "${RED}QnA Agent Infrastructure Teardown${NC}"
    echo "=============================================="
    echo ""
    echo -e "${YELLOW}WARNING: This will destroy ALL infrastructure resources!${NC}"
    echo ""

    # Check for --force flag
    if [[ "${1:-}" != "--force" ]]; then
        echo "Add --force flag to skip this confirmation"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Teardown cancelled"
            exit 0
        fi
    fi

    check_command terraform
    validate_env
    terraform_destroy
    cleanup_kubeconfig
    print_summary
}

# Run main
main "$@"
