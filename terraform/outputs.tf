output "server_ip" {
  description = "Public IP of the k3s server"
  value       = module.hetzner.server_ip
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "scp root@${module.hetzner.server_ip}:/etc/rancher/k3s/k3s.yaml ~/.kube/config"
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "http://${module.hetzner.server_ip}"
}
