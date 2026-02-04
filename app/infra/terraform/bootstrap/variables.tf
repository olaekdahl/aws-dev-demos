variable "aws_region" {
  type        = string
  description = "AWS region for the bootstrap resources (Terraform state bucket)."
  default     = "us-west-2"
}

variable "project_name" {
  type        = string
  description = "Prefix for resource names."
  default     = "code-quiz"
}
