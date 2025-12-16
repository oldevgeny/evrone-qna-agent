# Default deny all ingress and egress traffic
resource "kubernetes_network_policy" "default_deny" {
  metadata {
    name      = "default-deny-all"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {}

    policy_types = ["Ingress", "Egress"]
  }
}

# Allow DNS egress for all pods
resource "kubernetes_network_policy" "allow_dns" {
  metadata {
    name      = "allow-dns"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = "kube-system"
          }
        }
      }

      ports {
        protocol = "UDP"
        port     = "53"
      }
      ports {
        protocol = "TCP"
        port     = "53"
      }
    }

    policy_types = ["Egress"]
  }
}

# Allow traffic to QnA Agent from Traefik ingress
resource "kubernetes_network_policy" "allow_qna_agent_ingress" {
  metadata {
    name      = "allow-qna-agent-ingress"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "qna-agent"
      }
    }

    ingress {
      # Allow from Traefik in kube-system
      from {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = "kube-system"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "8000"
      }
    }

    policy_types = ["Ingress"]
  }
}

# Allow QnA Agent to connect to PgBouncer
resource "kubernetes_network_policy" "allow_pgbouncer_from_qna" {
  metadata {
    name      = "allow-pgbouncer-from-qna"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "pgbouncer"
      }
    }

    ingress {
      from {
        pod_selector {
          match_labels = {
            app = "qna-agent"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "6432"
      }
    }

    policy_types = ["Ingress"]
  }
}

# Allow PgBouncer to connect to PostgreSQL
resource "kubernetes_network_policy" "allow_postgres_from_pgbouncer" {
  metadata {
    name      = "allow-postgres-from-pgbouncer"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "postgres"
      }
    }

    ingress {
      from {
        pod_selector {
          match_labels = {
            app = "pgbouncer"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "5432"
      }
    }

    policy_types = ["Ingress"]
  }
}

# Allow backup job to connect to PostgreSQL
resource "kubernetes_network_policy" "allow_postgres_from_backup" {
  metadata {
    name      = "allow-postgres-from-backup"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "postgres"
      }
    }

    ingress {
      from {
        pod_selector {
          match_labels = {
            app = "postgres-backup"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "5432"
      }
    }

    policy_types = ["Ingress"]
  }
}

# QnA Agent egress: PgBouncer + external APIs (LiteLLM, Langfuse)
resource "kubernetes_network_policy" "qna_agent_egress" {
  metadata {
    name      = "qna-agent-egress"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "qna-agent"
      }
    }

    # Allow to PgBouncer within namespace
    egress {
      to {
        pod_selector {
          match_labels = {
            app = "pgbouncer"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "6432"
      }
    }

    # Allow HTTPS to external APIs (LiteLLM, Langfuse)
    egress {
      ports {
        protocol = "TCP"
        port     = "443"
      }
    }

    policy_types = ["Egress"]
  }
}

# PgBouncer egress: PostgreSQL only
resource "kubernetes_network_policy" "pgbouncer_egress" {
  metadata {
    name      = "pgbouncer-egress"
    namespace = kubernetes_namespace.qna_agent.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "pgbouncer"
      }
    }

    egress {
      to {
        pod_selector {
          match_labels = {
            app = "postgres"
          }
        }
      }

      ports {
        protocol = "TCP"
        port     = "5432"
      }
    }

    policy_types = ["Egress"]
  }
}
