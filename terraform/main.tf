module "hetzner" {
  source = "./modules/hetzner"

  environment         = var.environment
  location            = var.location
  server_type         = var.server_type
  ssh_public_key_path = var.ssh_public_key_path
  admin_ips           = var.admin_ips
}

module "kubernetes" {
  source = "./modules/kubernetes"

  depends_on = [module.hetzner]

  domain                = var.domain
  acme_email            = var.acme_email
  db_password           = var.db_password
  litellm_api_key       = var.litellm_api_key
  langfuse_public_key   = var.langfuse_public_key
  langfuse_secret_key   = var.langfuse_secret_key
  app_image             = var.app_image
  app_image_pull_policy = var.app_image_pull_policy
}
