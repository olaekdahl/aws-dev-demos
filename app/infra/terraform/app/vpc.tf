data "aws_availability_zones" "available" {
  state = "available"

  # Filter out Local Zones and Wavelength Zones - they don't support many services
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.8"

  name = "${local.name}-vpc"
  cidr = "10.20.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, local.az_count)
  public_subnets  = ["10.20.0.0/20", "10.20.16.0/20"]
  private_subnets = ["10.20.128.0/20", "10.20.144.0/20"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = local.tags
}
