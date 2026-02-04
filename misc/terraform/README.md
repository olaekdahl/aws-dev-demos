# AWS Capstone Architecture - Terraform

Complete three-tier AWS architecture using Terraform, demonstrating enterprise-grade infrastructure patterns.

## Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                         VPC                             │
                    │  ┌───────────────────┐    ┌───────────────────┐         │
    Internet ──────►│  │  Public Subnet A  │    │  Public Subnet B  │         │
        │           │  │    (ALB, NAT)     │    │    (ALB, NAT)     │         │
        │           │  └─────────┬─────────┘    └─────────┬─────────┘         │
        │           │            │                        │                   │
        ▼           │  ┌─────────▼─────────┐    ┌─────────▼─────────┐         │
       ALB ────────►│  │   App Subnet A    │    │   App Subnet B    │         │
                    │  │   (EC2 ASG)       │    │   (EC2 ASG)       │         │
                    │  └─────────┬─────────┘    └─────────┬─────────┘         │
                    │            │                        │                   │
                    │  ┌─────────▼─────────┐    ┌─────────▼─────────┐         │
                    │  │    DB Subnet A    │    │    DB Subnet B    │         │
                    │  │  (Aurora + EFS)   │    │  (Aurora + EFS)   │         │
                    │  └───────────────────┘    └───────────────────┘         │
                    └─────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| [main.tf](main.tf) | Provider configuration, data sources |
| [variables.tf](variables.tf) | Input variables with defaults |
| [network.tf](network.tf) | VPC, subnets, route tables, NAT gateway |
| [security.tf](security.tf) | Security groups for ALB, app, DB tiers |
| [alb.tf](alb.tf) | Application Load Balancer configuration |
| [asg.tf](asg.tf) | Auto Scaling Group with launch template |
| [aurora.tf](aurora.tf) | Aurora PostgreSQL Serverless cluster |
| [efs.tf](efs.tf) | Elastic File System for shared storage |
| [outputs.tf](outputs.tf) | Exported values (ALB DNS, etc.) |

## Quick Start

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply

# Destroy when done
terraform destroy
```

## Configuration

Key variables in `variables.tf`:

```hcl
variable "region" {
  default = "us-east-1"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "app_instance_type" {
  default = "t3.small"
}

variable "app_desired_capacity" {
  default = 2
}
```

## Features Demonstrated

- **Multi-AZ Deployment**: High availability across two availability zones
- **Three-Tier Architecture**: Public, application, and database tiers
- **Auto Scaling**: EC2 instances scale based on demand
- **Aurora Serverless**: Cost-effective managed database
- **EFS**: Shared file system for application data
- **Security Groups**: Least-privilege network access
- **NAT Gateway**: Outbound internet for private subnets

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- IAM permissions for EC2, VPC, RDS, EFS, ELB

## Cost Considerations

This infrastructure will incur AWS charges for:
- NAT Gateway (hourly + data transfer)
- ALB (hourly + LCU)
- Aurora Serverless (ACU hours)
- EC2 instances (hourly)
- EFS (storage + throughput)

**Remember to destroy resources when not in use!**
