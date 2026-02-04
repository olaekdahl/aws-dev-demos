# Miscellaneous AWS Demos

Additional AWS demos organized by Infrastructure as Code (IaC) tool and programming language.

## Directory Structure

```
misc/
├── boto3-demos/         # Python AWS SDK demos
├── cloudformation/      # CloudFormation templates (YAML & JSON)
├── terraform/           # Terraform AWS infrastructure
├── cdk-s3-bucket/       # AWS CDK TypeScript example
└── dotnet-dynamodb/     # .NET DynamoDB demo
```

## Quick Links

| Folder | Description | Language/Tool |
|--------|-------------|---------------|
| [boto3-demos](boto3-demos/) | S3, EC2, DynamoDB operations | Python + boto3 |
| [cloudformation](cloudformation/) | IaC templates for EC2, DynamoDB, VPC | YAML/JSON |
| [terraform](terraform/) | Three-tier AWS architecture | HCL |
| [cdk-s3-bucket](cdk-s3-bucket/) | S3 bucket with CDK | TypeScript |
| [dotnet-dynamodb](dotnet-dynamodb/) | DynamoDB CRUD operations | C# / .NET |

## Overview by Category

### Python SDK (boto3)

Self-contained scripts demonstrating common AWS operations:
- S3: List by prefix, multipart upload, get object, client vs resource API
- EC2: List instances with details
- DynamoDB: Table creation (sync & async), Lambda handler

### Infrastructure as Code

**CloudFormation** - AWS native IaC:
- Simple EC2 instance
- EC2 with parameters and UserData
- DynamoDB table with configurable throughput
- AWS sample templates (S3 website, VPC)

**Terraform** - Multi-cloud IaC:
- Complete three-tier architecture
- VPC, ALB, Auto Scaling, Aurora, EFS
- Production-ready patterns

**CDK** - Programmatic IaC:
- TypeScript S3 bucket example
- Type-safe infrastructure definitions

### .NET SDK

C# examples comparing API styles:
- Document Model (high-level) API
- Low-Level API for fine-grained control

## Prerequisites

### Python
```bash
pip install boto3 aioboto3
```

### Terraform
```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://terraform.io
```

### CDK
```bash
npm install -g aws-cdk
```

### .NET
```bash
# Install .NET SDK from https://dotnet.microsoft.com
dotnet restore
```

## AWS Credentials

All demos require configured AWS credentials:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1

# Option 3: AWS profiles
aws configure --profile myprofile
# Then use --profile myprofile with demos
```
