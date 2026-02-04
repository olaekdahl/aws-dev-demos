import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { S3Client } from "@aws-sdk/client-s3";
import { SQSClient } from "@aws-sdk/client-sqs";
import { config, isS3PathStyle } from "../config";
import { AWSXRay } from "../observability/xray";

export function createDynamoDocClient() {
  const ddb = new DynamoDBClient({
    region: config.AWS_REGION,
    endpoint: config.DDB_ENDPOINT_URL
  });

  const traced = (AWSXRay as any)?.captureAWSv3Client ? (AWSXRay as any).captureAWSv3Client(ddb) : ddb;
  return DynamoDBDocumentClient.from(traced, {
    marshallOptions: { removeUndefinedValues: true }
  });
}

export function createS3Client() {
  const s3 = new S3Client({
    region: config.AWS_REGION,
    endpoint: config.S3_ENDPOINT_URL,
    forcePathStyle: isS3PathStyle()
  });
  return (AWSXRay as any)?.captureAWSv3Client ? (AWSXRay as any).captureAWSv3Client(s3) : s3;
}

export function createSqsClient() {
  const sqs = new SQSClient({
    region: config.AWS_REGION,
    endpoint: config.SQS_ENDPOINT_URL
  });
  return (AWSXRay as any)?.captureAWSv3Client ? (AWSXRay as any).captureAWSv3Client(sqs) : sqs;
}
