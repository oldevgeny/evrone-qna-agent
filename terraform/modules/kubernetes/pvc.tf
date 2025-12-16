resource "kubernetes_persistent_volume_claim" "postgres" {
  wait_until_bound = false

  metadata {
    name      = "postgres-pvc"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    access_modes = ["ReadWriteOnce"]

    resources {
      requests = {
        storage = "20Gi"
      }
    }

    storage_class_name = "local-path"
  }
}
