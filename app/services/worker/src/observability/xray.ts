import AWSXRay from "aws-xray-sdk-core";
import { isXrayDisabled } from "../config";
import { logger } from "../logger";

// CRITICAL: Set IGNORE_ERROR strategy at module load time, BEFORE any AWS clients
// are created with captureAWSv3Client. AWS SDK calls happen both inside and outside
// X-Ray segment context (e.g., SQS polling loop). Without this, every SQS
// ReceiveMessage call throws "Failed to get the current sub/segment from the context"
AWSXRay.setContextMissingStrategy("IGNORE_ERROR");

export function initXRay() {
  if (isXrayDisabled()) {
    logger.info("X-Ray disabled (XRAY_DISABLED=true)");
    return { enabled: false as const };
  }

  AWSXRay.setDaemonAddress(process.env.AWS_XRAY_DAEMON_ADDRESS || "127.0.0.1:2000");

  return { enabled: true as const };
}

export { AWSXRay };
