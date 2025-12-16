# ResourceQuota to limit namespace resource consumption
resource "kubernetes_resource_quota" "qna_agent" {
  metadata {
    name      = "qna-agent-quota"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"           = "4"
      "requests.memory"        = "4Gi"
      "limits.cpu"             = "8"
      "limits.memory"          = "8Gi"
      "pods"                   = "20"
      "services"               = "10"
      "secrets"                = "20"
      "configmaps"             = "20"
      "persistentvolumeclaims" = "10"
    }
  }
}

# LimitRange for default resource constraints
resource "kubernetes_limit_range" "qna_agent" {
  metadata {
    name      = "qna-agent-limits"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    limit {
      type = "Container"

      default = {
        cpu    = "500m"
        memory = "512Mi"
      }

      default_request = {
        cpu    = "100m"
        memory = "128Mi"
      }

      max = {
        cpu    = "2"
        memory = "2Gi"
      }

      min = {
        cpu    = "50m"
        memory = "64Mi"
      }
    }

    limit {
      type = "PersistentVolumeClaim"

      max = {
        storage = "50Gi"
      }

      min = {
        storage = "1Gi"
      }
    }
  }
}
