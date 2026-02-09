# AWS Account Reset Tool

A Python script to reset an AWS account to a clean state by deleting all user-created resources.

## ⚠️ WARNING

**This script is DESTRUCTIVE!** It will delete:
- All S3 buckets and their contents
- All DynamoDB tables
- All Lambda functions
- All API Gateway APIs
- All SQS queues and SNS topics
- All EventBridge rules
- All CloudWatch alarms, dashboards, and log groups
- All Cognito user pools and identity pools
- All EC2 instances, volumes, snapshots, security groups
- All IAM users (except preserved ones), roles, groups, and policies
- All CloudFormation stacks
- All Secrets Manager secrets
- All Step Functions state machines
- All ECR repositories
- All customer-managed KMS keys (scheduled for deletion)

## What Is Preserved

- **Root account** (cannot be deleted)
- **IAM user: `ola-admin`** (configurable in script)
- **AWS-managed policies and roles**
- **AWS service-linked roles**
- **Default VPCs and security groups**

## Prerequisites

```bash
pip install boto3
```

Ensure your AWS credentials are configured:
```bash
aws configure
# or
export AWS_PROFILE=your-profile
```

## Usage

### Step 1: Dry Run (Preview)

Always run a dry run first to see what would be deleted:

```bash
python3 reset_aws_account.py --dry-run
```

This will list all resources that would be deleted without actually deleting anything.

### Step 2: Execute (Delete)

After reviewing the dry run output, execute the deletion:

```bash
python3 reset_aws_account.py --execute
```

You'll have 10 seconds to cancel (Ctrl+C) after starting.

### Optional: Limit to Specific Regions

```bash
python3 reset_aws_account.py --dry-run --regions us-east-1 us-west-2
python3 reset_aws_account.py --execute --regions us-east-1 us-west-2
```

## Customization

### Preserve Additional IAM Users

Edit the script and add users to the `PRESERVE_IAM_USERS` set:

```python
PRESERVE_IAM_USERS = {"ola-admin", "another-user", "ci-user"}
```

### Add/Remove Regions

Edit the `REGIONS_TO_CLEAN` list in the script:

```python
REGIONS_TO_CLEAN = [
    "us-east-1", "us-west-2", "eu-west-1"
]
```

## Order of Operations

The script deletes resources in dependency order:

1. **S3 Buckets** (global) - with all objects and versions
2. **IAM Resources** (global) - policies, roles, users, groups
3. **Per Region:**
   - CloudFormation Stacks (this may delete many resources)
   - Lambda Functions
   - API Gateways (REST and HTTP)
   - Step Functions
   - SQS Queues
   - SNS Topics
   - EventBridge Rules and Buses
   - DynamoDB Tables
   - Cognito Pools
   - Secrets
   - ECR Repositories
   - CloudWatch Resources
   - EC2 Resources
   - KMS Keys (scheduled, 7-day window)

## Known Limitations

1. **Some resources may fail to delete** if they have dependencies not handled by this script
2. **VPCs with custom subnets** are not deleted (to avoid complexity with NAT gateways, etc.)
3. **RDS databases** are not included - add if needed
4. **EKS clusters** are not included - add if needed
5. **CloudFront distributions** are not included - add if needed

## Troubleshooting

If resources fail to delete:

1. Check the error messages in the output
2. Some resources may need manual deletion due to:
   - Active deletion protection
   - Cross-resource dependencies
   - Resources created by AWS services

## After Running

After the script completes:

1. Review any errors in the output
2. Check the AWS Console for any remaining resources
3. Some resources (like KMS keys) are only scheduled for deletion with a 7-day waiting period

## Example Output

```
[DRY-RUN] [INFO] === Cleaning S3 Buckets ===
[DRY-RUN] [INFO] Would delete: S3 Bucket - my-demo-bucket (global)
[DRY-RUN] [INFO] Would delete: S3 Bucket - another-bucket (global)
[DRY-RUN] [INFO] === Cleaning IAM Resources (Global) ===
[DRY-RUN] [INFO] Would delete: IAM Policy - MyCustomPolicy
[DRY-RUN] [INFO] Preserving IAM User: ola-admin
...
============================================================
CLEANUP SUMMARY
============================================================

Resources to delete: 47
Errors encountered: 0

✅ Dry run complete. Run with --execute to actually delete resources.
```
