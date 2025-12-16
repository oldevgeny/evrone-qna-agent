# PodDisruptionBudget for QnA Agent - ensure at least 1 replica during updates
resource "kubernetes_pod_disruption_budget_v1" "qna_agent" {
  metadata {
    name      = "qna-agent-pdb"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    min_available = 1

    selector {
      match_labels = {
        app = "qna-agent"
      }
    }
  }
}

# PodDisruptionBudget for PgBouncer - ensure at least 1 replica during updates
resource "kubernetes_pod_disruption_budget_v1" "pgbouncer" {
  metadata {
    name      = "pgbouncer-pdb"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    min_available = 1

    selector {
      match_labels = {
        app = "pgbouncer"
      }
    }
  }
}

# PodDisruptionBudget for PostgreSQL - allow 0 disruptions (single replica)
resource "kubernetes_pod_disruption_budget_v1" "postgres" {
  metadata {
    name      = "postgres-pdb"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    max_unavailable = 0

    selector {
      match_labels = {
        app = "postgres"
      }
    }
  }
}
