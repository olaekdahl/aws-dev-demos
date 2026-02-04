import AWSXRay from "aws-xray-sdk-core";
import * as xrayExpress from "aws-xray-sdk-express";
import { isXrayDisabled } from "../config";
import { logger } from "../logger";

export function initXRay() {
  if (isXrayDisabled()) {
    logger.info("X-Ray disabled (XRAY_DISABLED=true)");
    return { enabled: false as const };
  }

  // Capture outbound HTTP(S)
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const http = require("http");
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const https = require("https");
    AWSXRay.captureHTTPsGlobal(http);
    AWSXRay.captureHTTPsGlobal(https);
  } catch (e) {
    logger.warn({ err: e }, "Unable to enable global HTTP capture for X-Ray");
  }

  AWSXRay.setDaemonAddress(process.env.AWS_XRAY_DAEMON_ADDRESS || "127.0.0.1:2000");

  return { enabled: true as const };
}

// Attach express middleware to AWSXRay for compatibility with app.ts usage
const AWSXRayWithExpress = Object.assign(AWSXRay, { express: xrayExpress });

export { AWSXRayWithExpress as AWSXRay };
