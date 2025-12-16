resource "kubernetes_stateful_set" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    service_name = "postgres"
    replicas     = 1

    selector {
      match_labels = {
        app = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }

      spec {
        service_account_name            = kubernetes_service_account.postgres.metadata[0].name
        automount_service_account_token = false

        container {
          name  = "postgres"
          image = "postgres:18.1-bookworm"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_USER"
            value = "qna"
          }

          env {
            name  = "POSTGRES_DB"
            value = "qna"
          }

          env {
            name  = "PGDATA"
            value = "/var/lib/postgresql/data/pgdata"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }

          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }

          volume_mount {
            name       = "run-postgresql"
            mount_path = "/run/postgresql"
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

          startup_probe {
            exec {
              command = ["pg_isready", "-U", "qna", "-d", "qna"]
            }
            period_seconds    = 5
            failure_threshold = 30
          }

          liveness_probe {
            exec {
              command = ["pg_isready", "-U", "qna", "-d", "qna"]
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          readiness_probe {
            exec {
              command = ["pg_isready", "-U", "qna", "-d", "qna"]
            }
            initial_delay_seconds = 5
            period_seconds        = 5
            timeout_seconds       = 2
            failure_threshold     = 3
            success_threshold     = 1
          }

          security_context {
            run_as_non_root            = true
            run_as_user                = 999
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

        security_context {
          fs_group        = 999
          run_as_non_root = true
          run_as_user     = 999
          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        volume {
          name = "postgres-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.postgres.metadata[0].name
          }
        }

        volume {
          name = "tmp"
          empty_dir {}
        }

        volume {
          name = "run-postgresql"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    selector = {
      app = "postgres"
    }

    port {
      port        = 5432
      target_port = 5432
    }

    cluster_ip = "None"
  }
}
