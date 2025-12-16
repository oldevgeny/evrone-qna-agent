variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for server access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Hetzner Cloud location"
  type        = string
  default     = "nbg1"
}

variable "server_type" {
  description = "Hetzner Cloud server type"
  type        = string
  default     = "cx22"
}

variable "domain" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "acme_email" {
  description = "Email for Let's Encrypt certificates"
  type        = string
  default     = ""
}

variable "db_password" {
  description = "PostgreSQL database password. Required - set via TF_VAR_db_password environment variable."
  type        = string
  sensitive   = true
}

variable "litellm_api_key" {
  description = "LiteLLM/OpenRouter API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_public_key" {
  description = "Langfuse public key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "admin_ips" {
  description = "IP addresses allowed for SSH and Kubernetes API access (CIDR format). Required - no default for security."
  type        = list(string)
}

variable "app_image" {
  description = "QnA Agent container image with tag (e.g., ghcr.io/org/qna-agent:v1.0.0)"
  type        = string
  default     = "docker.io/library/qna-agent:latest"
}

variable "app_image_pull_policy" {
  description = "Image pull policy (Always, IfNotPresent, Never)"
  type        = string
  default     = "IfNotPresent"
}
