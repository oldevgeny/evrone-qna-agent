# IngressRoute for domain-based HTTPS access
resource "kubernetes_manifest" "ingressroute" {
  count = var.domain != "" ? 1 : 0

  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "IngressRoute"

    metadata = {
      name      = "qna-agent"
      namespace = kubernetes_namespace.qna_agent.metadata[0].name
    }

    spec = {
      entryPoints = ["websecure"]

      routes = [
        {
          match = "Host(`${var.domain}`)"
          kind  = "Rule"
          middlewares = [
            {
              name      = "ratelimit"
              namespace = kubernetes_namespace.qna_agent.metadata[0].name
            },
            {
              name      = "security-headers"
              namespace = kubernetes_namespace.qna_agent.metadata[0].name
            }
          ]
          services = [
            {
              name = "qna-agent"
              port = 80
            }
          ]
        }
      ]

      tls = {
        certResolver = "letsencrypt"
      }
    }
  }
}

# IngressRoute for IP-based HTTP access (when no domain configured)
resource "kubernetes_manifest" "ingressroute_http" {
  count = var.domain == "" ? 1 : 0

  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "IngressRoute"

    metadata = {
      name      = "qna-agent-http"
      namespace = kubernetes_namespace.qna_agent.metadata[0].name
    }

    spec = {
      entryPoints = ["web"]

      routes = [
        {
          match = "PathPrefix(`/`)"
          kind  = "Rule"
          middlewares = [
            {
              name      = "security-headers"
              namespace = kubernetes_namespace.qna_agent.metadata[0].name
            }
          ]
          services = [
            {
              name = "qna-agent"
              port = 80
            }
          ]
        }
      ]
    }
  }
}

resource "kubernetes_manifest" "middleware_ratelimit" {
  count = var.domain != "" ? 1 : 0

  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "Middleware"

    metadata = {
      name      = "ratelimit"
      namespace = kubernetes_namespace.qna_agent.metadata[0].name
    }

    spec = {
      rateLimit = {
        average = 100
        burst   = 50
      }
    }
  }
}

# Security headers middleware
resource "kubernetes_manifest" "middleware_security_headers" {
  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "Middleware"

    metadata = {
      name      = "security-headers"
      namespace = kubernetes_namespace.qna_agent.metadata[0].name
    }

    spec = {
      headers = {
        frameDeny            = true
        browserXssFilter     = true
        contentTypeNosniff   = true
        stsSeconds           = 31536000
        stsIncludeSubdomains = true
        stsPreload           = true
        customResponseHeaders = {
          "X-Frame-Options"        = "DENY"
          "X-Content-Type-Options" = "nosniff"
          "X-XSS-Protection"       = "1; mode=block"
          "Referrer-Policy"        = "strict-origin-when-cross-origin"
        }
      }
    }
  }
}
