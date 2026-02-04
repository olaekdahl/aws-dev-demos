# AWS CDK S3 Bucket Example

Demonstrates creating an S3 bucket using the AWS Cloud Development Kit (CDK) with TypeScript.

## What This Creates

A simple S3 bucket with:
- Auto-deletion enabled (for demo purposes)
- Removal policy set to DESTROY
- Versioning disabled

## Prerequisites

```bash
# Install CDK CLI globally
npm install -g aws-cdk

# Configure AWS credentials
aws configure
```

## Quick Start

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only per account/region)
cdk bootstrap

# Preview CloudFormation template
cdk synth

# Deploy the stack
cdk deploy

# Destroy when done
cdk destroy
```

## Project Structure

```
├── bin/                     # CDK app entry point
│   └── cdk-s3-example.ts
├── lib/                     # Stack definitions
│   └── cdk-s3-example-stack.ts
├── test/                    # Unit tests
├── cdk.json                 # CDK configuration
├── package.json             # Node.js dependencies
└── tsconfig.json            # TypeScript configuration
```

## Stack Code

```typescript
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class CdkS3ExampleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new s3.Bucket(this, 'DemoBucket', {
      versioned: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });
  }
}
```

## Useful CDK Commands

| Command | Description |
|---------|-------------|
| `npm run build` | Compile TypeScript to JavaScript |
| `npm run watch` | Watch for changes and compile |
| `npm run test` | Run Jest unit tests |
| `npx cdk deploy` | Deploy stack to AWS |
| `npx cdk diff` | Compare deployed vs local |
| `npx cdk synth` | Output CloudFormation template |
| `npx cdk destroy` | Remove stack from AWS |

## Why CDK?

- **Type safety**: TypeScript catches errors at compile time
- **Abstractions**: High-level constructs simplify common patterns
- **Reusability**: Share infrastructure as code libraries
- **Testing**: Unit test your infrastructure code
- **IDE support**: Autocomplete and documentation in editor
