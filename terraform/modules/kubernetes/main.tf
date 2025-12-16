variable "domain" {
  type = string
}

variable "acme_email" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "litellm_api_key" {
  type      = string
  sensitive = true
}

variable "langfuse_public_key" {
  type      = string
  sensitive = true
}

variable "langfuse_secret_key" {
  type      = string
  sensitive = true
}

variable "app_image" {
  type        = string
  description = "QnA Agent container image with tag"
}

variable "app_image_pull_policy" {
  type        = string
  description = "Image pull policy"
}

resource "kubernetes_namespace" "qna_agent" {
  metadata {
    name = "qna-agent"

    labels = {
      app = "qna-agent"
      # Pod Security Standards - enforce restricted profile
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/audit"   = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}
