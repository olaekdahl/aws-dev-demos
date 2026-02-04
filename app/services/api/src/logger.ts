import pino from "pino";
import { config } from "./config";

export const logger = pino({
  level: config.LOG_LEVEL,
  base: {
    service: config.SERVICE_NAME
  },
  redact: {
    paths: ["req.headers.authorization"],
    remove: true
  }
});
