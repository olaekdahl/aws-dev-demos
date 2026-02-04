variable "aws_region" {
  type        = string
  description = "AWS region to deploy into."
  default     = "us-west-2"
}

variable "project_name" {
  type        = string
  description = "Prefix for resource names."
  default     = "code-quiz"
}

variable "domain_name" {
  type        = string
  description = "Root domain name hosted in Route53 (e.g. code-quiz.io)."
  default     = "code-quiz.io"
}

variable "enable_ecs_services" {
  type        = bool
  description = "Set false for initial infra bootstrap (ECR, VPC, ALB, etc). Set true after images are pushed to ECR."
  default     = false
}

variable "desired_count_web" {
  type        = number
  default     = 2
}

variable "desired_count_api" {
  type        = number
  default     = 2
}

variable "desired_count_worker" {
  type        = number
  default     = 2
}

variable "web_image" {
  type        = string
  description = "Full image URI for the web container (ECR URI + tag)."
  default     = ""
}

variable "api_image" {
  type        = string
  description = "Full image URI for the api container (ECR URI + tag)."
  default     = ""
}

variable "worker_image" {
  type        = string
  description = "Full image URI for the worker container (ECR URI + tag)."
  default     = ""
}

variable "github_repo" {
  type        = string
  description = "GitHub repository in the form owner/repo (used for OIDC trust)."
  default     = ""
}

variable "github_branch" {
  type        = string
  description = "Branch allowed to deploy (used for OIDC trust)."
  default     = "main"
}
