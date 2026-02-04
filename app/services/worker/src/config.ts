import { z } from "zod";

const boolFromEnv = (v: string | undefined) =>
  v === "1" || v?.toLowerCase() === "true" || v?.toLowerCase() === "yes";

const schema = z.object({
  NODE_ENV: z.string().default("production"),
  LOG_LEVEL: z.string().default("info"),
  SERVICE_NAME: z.string().default("code-quiz-worker"),

  AWS_REGION: z.string().default("us-west-2"),
  DDB_ENDPOINT_URL: z.string().optional(),
  S3_ENDPOINT_URL: z.string().optional(),
  SQS_ENDPOINT_URL: z.string().optional(),
  S3_FORCE_PATH_STYLE: z.string().optional(),

  DDB_TABLE_QUIZZES: z.string().min(1),
  DDB_TABLE_ATTEMPTS: z.string().min(1),
  DDB_TABLE_EXPORTS: z.string().min(1),
  S3_BUCKET: z.string().min(1),
  SQS_QUEUE_URL: z.string().min(1),

  WORKER_POLL_INTERVAL_MS: z.coerce.number().int().positive().default(2000),
  WORKER_MAX_MESSAGES: z.coerce.number().int().min(1).max(10).default(10),
  XRAY_DISABLED: z.string().optional()
});

export type WorkerConfig = z.infer<typeof schema>;
export const config: WorkerConfig = schema.parse(process.env);

export const isXrayDisabled = () => boolFromEnv(config.XRAY_DISABLED);
export const isS3PathStyle = () => boolFromEnv(config.S3_FORCE_PATH_STYLE);
