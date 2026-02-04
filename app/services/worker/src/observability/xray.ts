import AWSXRay from "aws-xray-sdk-core";
import { isXrayDisabled } from "../config";
import { logger } from "../logger";

export function initXRay() {
  if (isXrayDisabled()) {
    logger.info("X-Ray disabled (XRAY_DISABLED=true)");
    // Prevent errors when AWS SDK calls happen outside X-Ray context
    AWSXRay.setContextMissingStrategy("IGNORE_ERROR");
    return { enabled: false as const };
  }

  AWSXRay.setDaemonAddress(process.env.AWS_XRAY_DAEMON_ADDRESS || "127.0.0.1:2000");

  return { enabled: true as const };
}

export { AWSXRay };
