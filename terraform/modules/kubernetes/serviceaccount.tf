# ServiceAccount for QnA Agent
resource "kubernetes_service_account" "qna_agent" {
  metadata {
    name      = "qna-agent"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  automount_service_account_token = false
}

# ServiceAccount for PostgreSQL
resource "kubernetes_service_account" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  automount_service_account_token = false
}

# ServiceAccount for PgBouncer
resource "kubernetes_service_account" "pgbouncer" {
  metadata {
    name      = "pgbouncer"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  automount_service_account_token = false
}

# ServiceAccount for Backup Jobs
resource "kubernetes_service_account" "backup" {
  metadata {
    name      = "postgres-backup"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  automount_service_account_token = false
}

# Role for backup job - minimal permissions to read secrets
resource "kubernetes_role" "backup" {
  metadata {
    name      = "postgres-backup-role"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["secrets"]
    verbs      = ["get"]
    resource_names = [
      kubernetes_secret.postgres.metadata[0].name
    ]
  }
}

# RoleBinding for backup ServiceAccount
resource "kubernetes_role_binding" "backup" {
  metadata {
    name      = "postgres-backup-binding"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.backup.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.backup.metadata[0].name
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }
}
