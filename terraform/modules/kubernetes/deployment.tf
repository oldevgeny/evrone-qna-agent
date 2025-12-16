resource "kubernetes_deployment" "qna_agent" {
  metadata {
    name      = "qna-agent"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "qna-agent"
      }
    }

    template {
      metadata {
        labels = {
          app = "qna-agent"
        }
      }

      spec {
        service_account_name            = kubernetes_service_account.qna_agent.metadata[0].name
        automount_service_account_token = false

        security_context {
          fs_group        = 1000
          run_as_non_root = true
          run_as_user     = 1000
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        container {
          name              = "qna-agent"
          image             = var.app_image
          image_pull_policy = var.app_image_pull_policy

          port {
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.qna_agent.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.qna_agent.metadata[0].name
            }
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health/live"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/health/ready"
              port = 8000
            }
            initial_delay_seconds = 5
            period_seconds        = 5
            timeout_seconds       = 2
            failure_threshold     = 3
            success_threshold     = 1
          }

          security_context {
            run_as_non_root            = true
            run_as_user                = 1000
            read_only_root_filesystem  = true
            allow_privilege_escalation = false
            capabilities {
              drop = ["ALL"]
            }
            seccomp_profile {
              type = "RuntimeDefault"
            }
          }
        }

      }
    }
  }

  depends_on = [kubernetes_deployment.pgbouncer]
}
