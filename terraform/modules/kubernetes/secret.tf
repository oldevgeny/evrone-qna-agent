resource "kubernetes_secret" "qna_agent" {
  metadata {
    name      = "qna-agent-secrets"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  data = {
    DATABASE_URL        = "postgresql+asyncpg://qna:${var.db_password}@pgbouncer:6432/qna"
    DB_PASSWORD         = var.db_password
    LITELLM_API_KEY     = var.litellm_api_key
    LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
    LANGFUSE_SECRET_KEY = var.langfuse_secret_key
  }

  type = "Opaque"
}

resource "kubernetes_secret" "postgres" {
  metadata {
    name      = "postgres-secrets"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  data = {
    POSTGRES_PASSWORD = var.db_password
  }

  type = "Opaque"
}
