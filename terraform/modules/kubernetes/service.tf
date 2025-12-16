resource "kubernetes_service" "qna_agent" {
  metadata {
    name      = "qna-agent"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    selector = {
      app = "qna-agent"
    }

    port {
      port        = 80
      target_port = 8000
    }

    type = "ClusterIP"
  }
}
