terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.45"
    }
  }
}

provider "aws" {
  region = var.region
}

# Data helpers
# Pick only REGIONAL AZs (exclude Local Zones, Wavelength, etc.)
data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "zone-type"
    values = ["availability-zone"]
  }

  # Avoid disabled AZs
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required", "opted-in"]
  }
}

# Use the first two regional AZs consistently
locals {
  selected_azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# Latest Amazon Linux 2023 x86_64 AMI (for app servers)
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}