# CloudFormation Templates

Collection of AWS CloudFormation templates demonstrating Infrastructure as Code (IaC) patterns.

## Templates

### Basic Examples

| Template | Description |
|----------|-------------|
| [ec2_simple.yaml](ec2_simple.yaml) | Minimal EC2 instance - simplest possible template |
| [ec2_with_parameters.yaml](ec2_with_parameters.yaml) | EC2 with parameters, UserData, and tags |
| [dynamodb_table.json](dynamodb_table.json) | DynamoDB table with configurable throughput (JSON format) |

### AWS Sample Templates

Templates from the [AWS CloudFormation Sample Templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-sample-templates.html):

| Template | Description |
|----------|-------------|
| [aws-samples/s3_website_cloudfront.json](aws-samples/s3_website_cloudfront.json) | S3 static website with CloudFront CDN and Route53 DNS |
| [aws-samples/vpc_public_dns.json](aws-samples/vpc_public_dns.json) | VPC with public subnets, DNS, and bastion host |

## Usage

### Deploy a Stack

```bash
# Simple deployment (no parameters)
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://ec2_simple.yaml

# With parameters
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://ec2_with_parameters.yaml \
  --parameters ParameterKey=ImageId,ParameterValue=ami-0440d3b780d96b29d

# With capabilities (for IAM resources)
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM
```

### Monitor Stack Status

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name my-stack

# Watch stack events
aws cloudformation describe-stack-events --stack-name my-stack

# Wait for completion
aws cloudformation wait stack-create-complete --stack-name my-stack
```

### Update a Stack

```bash
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://updated-template.yaml
```

### Delete a Stack

```bash
# Delete stack
aws cloudformation delete-stack --stack-name my-stack

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name my-stack
```

## Key Concepts Demonstrated

- **Parameters**: Accepting user input with validation
- **Mappings**: Region-specific values and lookups
- **Resources**: AWS resource definitions
- **Outputs**: Exporting values for other stacks
- **Intrinsic Functions**: !Ref, !Sub, !GetAtt, Fn::Join
- **UserData**: Instance initialization scripts
- **Tags**: Resource metadata and organization

## YAML vs JSON

CloudFormation supports both YAML and JSON formats:

- **YAML**: More readable, supports comments, less verbose
- **JSON**: Original format, wider tool support, stricter syntax

Both formats are functionally equivalent.
