import express from "express";
import cors from "cors";
import helmet from "helmet";
import pinoHttp from "pino-http";
import { logger } from "./logger";
import { AWSXRay } from "./observability/xray";

import { QuizzesRepository } from "./repositories/quizzes";
import { AttemptsRepository } from "./repositories/attempts";
import { ExportsRepository } from "./repositories/exports";
import { createDynamoDocClient, createS3Client, createSqsClient } from "./aws/clients";
import { JobsQueue } from "./aws/jobsQueue";

import { quizzesRoutes } from "./routes/quizzes";
import { attemptsRoutes } from "./routes/attempts";
import { exportsRoutes } from "./routes/exports";
import { errorHandler } from "./middleware/errorHandler";
import { config, isXrayDisabled } from "./config";

export function buildApp() {
  const app = express();

  // X-Ray segment around the whole request (optional)
  if (!isXrayDisabled()) {
    app.use(AWSXRay.express.openSegment(config.SERVICE_NAME));
  }

  app.use(
    pinoHttp({
      logger,
      autoLogging: true,
      customProps: (req) => ({ requestId: req.id })
    })
  );

  app.use(helmet());
  app.use(cors());
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (_req, res) => res.json({ ok: true }));

  const ddb = createDynamoDocClient();
  const s3 = createS3Client();
  const sqs = createSqsClient();

  const quizzesRepo = new QuizzesRepository(ddb);
  const attemptsRepo = new AttemptsRepository(ddb);
  const exportsRepo = new ExportsRepository(ddb);
  const jobs = new JobsQueue(sqs);

  app.use("/api/quizzes", quizzesRoutes({ quizzesRepo, attemptsRepo, exportsRepo, jobs }));
  app.use("/api/attempts", attemptsRoutes({ attemptsRepo }));
  app.use("/api/exports", exportsRoutes({ exportsRepo, s3 }));

  app.use(errorHandler);

  if (!isXrayDisabled()) {
    app.use(AWSXRay.express.closeSegment());
  }

  return app;
}
