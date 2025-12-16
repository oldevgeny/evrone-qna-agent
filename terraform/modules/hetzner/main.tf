terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = ">= 1.57.0, < 2.0.0"
    }
  }
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "server_type" {
  type = string
}

variable "ssh_public_key_path" {
  type = string
}

variable "admin_ips" {
  description = "IP addresses allowed for SSH and Kubernetes API access (CIDR format)"
  type        = list(string)
}

output "server_ip" {
  value = hcloud_server.k3s.ipv4_address
}
