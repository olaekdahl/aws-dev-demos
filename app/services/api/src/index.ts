import { buildApp } from "./app";
import { config } from "./config";
import { logger } from "./logger";
import { initXRay } from "./observability/xray";

initXRay();

const app = buildApp();

const server = app.listen(config.PORT, () => {
  logger.info({ port: config.PORT }, "API server listening");
});

// Graceful shutdown
function shutdown(signal: string) {
  logger.info({ signal }, "Shutting down");
  server.close(() => {
    logger.info("HTTP server closed");
    process.exit(0);
  });
  setTimeout(() => {
    logger.error("Force exiting after timeout");
    process.exit(1);
  }, 10_000).unref();
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
