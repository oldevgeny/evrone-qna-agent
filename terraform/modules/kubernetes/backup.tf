# Daily PostgreSQL backup CronJob
resource "kubernetes_cron_job_v1" "postgres_backup" {
  metadata {
    name      = "postgres-backup"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    schedule                      = "0 2 * * *" # Daily at 2 AM
    concurrency_policy            = "Forbid"
    successful_jobs_history_limit = 3
    failed_jobs_history_limit     = 1

    job_template {
      metadata {}

      spec {
        template {
          metadata {
            labels = {
              app = "postgres-backup"
            }
          }

          spec {
            service_account_name            = kubernetes_service_account.backup.metadata[0].name
            automount_service_account_token = false
            restart_policy                  = "OnFailure"

            security_context {
              fs_group        = 70
              run_as_non_root = true
              run_as_user     = 70
              seccomp_profile {
                type = "RuntimeDefault"
              }
            }

            container {
              name  = "backup"
              image = "postgres:16-alpine"

              command = ["/bin/sh", "-c"]
              args = [
                <<-EOT
                set -e
                BACKUP_FILE="/backups/qna-$(date +%Y%m%d-%H%M%S).sql.gz"
                echo "Starting backup to $BACKUP_FILE"
                PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h postgres -U qna -d qna | gzip > "$BACKUP_FILE"
                echo "Backup completed: $BACKUP_FILE"

                # Keep only last 7 days of backups
                find /backups -name "qna-*.sql.gz" -mtime +7 -delete
                echo "Cleanup completed"

                # List current backups
                ls -la /backups/
                EOT
              ]

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
                name       = "backup-storage"
                mount_path = "/backups"
              }

              volume_mount {
                name       = "tmp"
                mount_path = "/tmp"
              }

              resources {
                requests = {
                  memory = "128Mi"
                  cpu    = "100m"
                }
                limits = {
                  memory = "256Mi"
                  cpu    = "200m"
                }
              }

              security_context {
                run_as_non_root            = true
                run_as_user                = 70 # postgres user in alpine
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
              name = "backup-storage"
              persistent_volume_claim {
                claim_name = kubernetes_persistent_volume_claim.backups.metadata[0].name
              }
            }

            volume {
              name = "tmp"
              empty_dir {
                size_limit = "100Mi"
              }
            }
          }
        }
      }
    }
  }
}

# PVC for backup storage
resource "kubernetes_persistent_volume_claim" "backups" {
  metadata {
    name      = "backups-pvc"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "local-path"

    resources {
      requests = {
        storage = "5Gi"
      }
    }
  }

  wait_until_bound = false
}
