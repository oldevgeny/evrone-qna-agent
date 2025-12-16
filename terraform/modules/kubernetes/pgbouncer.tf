resource "kubernetes_config_map" "pgbouncer" {
  metadata {
    name      = "pgbouncer-config"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  data = {
    "pgbouncer.ini" = <<-EOT
      [databases]
      qna = host=postgres port=5432 dbname=qna

      [pgbouncer]
      listen_addr = 0.0.0.0
      listen_port = 6432
      auth_type = scram-sha-256
      auth_file = /etc/pgbouncer/userlist.txt
      pool_mode = session
      max_client_conn = 100
      default_pool_size = 25
      min_pool_size = 5
      reserve_pool_size = 5
      server_reset_query = DISCARD ALL
      log_connections = 1
      log_disconnections = 1
      log_pooler_errors = 1
      stats_period = 60
      ignore_startup_parameters = extra_float_digits
      admin_users = qna
    EOT
  }
}

resource "kubernetes_secret" "pgbouncer_userlist" {
  metadata {
    name      = "pgbouncer-userlist"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  data = {
    "userlist.txt" = "\"qna\" \"${var.db_password}\""
  }
}

resource "kubernetes_deployment" "pgbouncer" {
  metadata {
    name      = "pgbouncer"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "pgbouncer"
      }
    }

    template {
      metadata {
        labels = {
          app = "pgbouncer"
        }
      }

      spec {
        service_account_name            = kubernetes_service_account.pgbouncer.metadata[0].name
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
          name  = "pgbouncer"
          image = "ghcr.io/icoretech/pgbouncer-docker:1.24.1"

          port {
            container_port = 6432
          }

          volume_mount {
            name       = "pgbouncer-config"
            mount_path = "/etc/pgbouncer/pgbouncer.ini"
            sub_path   = "pgbouncer.ini"
            read_only  = true
          }

          volume_mount {
            name       = "pgbouncer-userlist"
            mount_path = "/etc/pgbouncer/userlist.txt"
            sub_path   = "userlist.txt"
            read_only  = true
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }

          resources {
            requests = {
              memory = "64Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "128Mi"
              cpu    = "200m"
            }
          }

          liveness_probe {
            tcp_socket {
              port = 6432
            }
            initial_delay_seconds = 10
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          readiness_probe {
            tcp_socket {
              port = 6432
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

        volume {
          name = "pgbouncer-config"
          config_map {
            name = kubernetes_config_map.pgbouncer.metadata[0].name
          }
        }

        volume {
          name = "pgbouncer-userlist"
          secret {
            secret_name = kubernetes_secret.pgbouncer_userlist.metadata[0].name
          }
        }

        volume {
          name = "tmp"
          empty_dir {}
        }
      }
    }
  }

  depends_on = [kubernetes_stateful_set.postgres]
}

resource "kubernetes_service" "pgbouncer" {
  metadata {
    name      = "pgbouncer"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    selector = {
      app = "pgbouncer"
    }

    port {
      port        = 6432
      target_port = 6432
    }
  }
}
