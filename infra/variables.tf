variable "region" {
  type    = string
  default = "ap-south-1"
}
variable "cluster_name" {
  type    = string
  default = "launchpad-eks"
}
variable "kubernetes_version" {
  type    = string
  default = "1.35"
}
variable "github_repository" {
  description = "Exact case-sensitive OWNER/REPO; production environment is restricted to main in GitHub."
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Use OWNER/REPO with no wildcard."
  }
}
variable "github_oidc_provider_arn" {
  description = "Existing token.actions.githubusercontent.com provider ARN, or null to create it."
  type        = string
  default     = null
}
