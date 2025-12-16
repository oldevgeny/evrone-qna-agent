terraform {
  required_version = ">= 1.5"

  # Terraform Cloud Backend (Recommended for production)
  # To enable:
  # 1. Create account at app.terraform.io
  # 2. Create organization and workspace with CLI-driven workflow
  # 3. Generate API token: terraform login
  # 4. Uncomment cloud block below
  # 5. Run: terraform init -migrate-state
  # 6. Delete local terraform.tfstate and terraform.tfstate.backup
  #
  # cloud {
  #   organization = "your-org-name"
  #   workspaces {
  #     name = "qna-agent-prod"
  #   }
  # }

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = ">= 1.57.0, < 2.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.38.0, < 3.0.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.17.0, < 3.0.0"
    }
  }
}
