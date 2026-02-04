import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class CdkS3ExampleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create an S3 bucket
    new s3.Bucket(this, 'ola-demo-004', {
      versioned: false, // Optional: Enable versioning
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Optional: Delete the bucket when the stack is deleted
      autoDeleteObjects: true, // Optional: Automatically delete objects in the bucket when the bucket is deleted
    });
  }
}

// npm install -g aws-cdk
// cdk init app --language typescript
// npm install @aws-cdk/aws-s3
// cdk bootstrap
// cdk deploy
// cdk destroy