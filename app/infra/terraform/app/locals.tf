locals {
  name = var.project_name

  tags = {
    project = var.project_name
  }

  az_count = 2
}
