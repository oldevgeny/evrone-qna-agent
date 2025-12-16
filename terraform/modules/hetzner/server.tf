resource "hcloud_ssh_key" "default" {
  name       = "qna-agent-${var.environment}"
  public_key = file(var.ssh_public_key_path)
}

resource "hcloud_server" "k3s" {
  name        = "qna-agent-k3s-${var.environment}"
  server_type = var.server_type
  location    = var.location
  image       = "ubuntu-24.04"

  ssh_keys = [hcloud_ssh_key.default.id]

  firewall_ids = [hcloud_firewall.k3s.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update system
    apt-get update && apt-get upgrade -y

    # Install k3s with secrets encryption enabled
    curl -sfL https://get.k3s.io | sh -s - \
      --disable traefik \
      --write-kubeconfig-mode 644 \
      --secrets-encryption

    # Wait for k3s to be ready
    until kubectl get nodes; do sleep 5; done

    # Install Traefik v3 via Helm
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

    helm repo add traefik https://traefik.github.io/charts
    helm repo update

    helm install traefik traefik/traefik \
      --namespace kube-system \
      --set image.tag=v3.6.4 \
      --set ports.web.port=80 \
      --set ports.websecure.port=443

    echo "k3s installation complete"
  EOF

  labels = {
    environment = var.environment
    role        = "k3s-server"
  }

  depends_on = [hcloud_network_subnet.main]
}

resource "hcloud_server_network" "k3s" {
  server_id  = hcloud_server.k3s.id
  network_id = hcloud_network.main.id
  ip         = "10.0.1.10"
}
