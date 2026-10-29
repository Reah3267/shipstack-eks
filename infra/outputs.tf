output "cluster_name" { value = aws_eks_cluster.lab.name }
output "region" { value = var.region }
output "github_role_arn" { value = aws_iam_role.deploy.arn }
output "ecr_registry" { value = split("/", aws_ecr_repository.service["tasks"].repository_url)[0] }
output "repositories" { value = { for k, r in aws_ecr_repository.service : k => r.repository_url } }
