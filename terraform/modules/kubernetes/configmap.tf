resource "kubernetes_config_map" "qna_agent" {
  metadata {
    name      = "qna-agent-config"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  data = {
    APP_NAME            = "QnA Agent API"
    DEBUG               = "false"
    LOG_LEVEL           = "INFO"
    LITELLM_API_BASE    = "https://openrouter.ai/api/v1"
    LITELLM_MODEL       = "openrouter/openai/gpt-4o-mini"
    LANGFUSE_HOST       = "https://cloud.langfuse.com"
    KNOWLEDGE_BASE_PATH = "/app/knowledge"
    HOST                = "0.0.0.0"
    PORT                = "8000"
  }
}
