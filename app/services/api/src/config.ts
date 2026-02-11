import { z } from "zod";

const boolFromEnv = (v: string | undefined) =>
  v === "1" || v?.toLowerCase() === "true" || v?.toLowerCase() === "yes";

const schema = z.object({
  NODE_ENV: z.string().default("production"),
  PORT: z.coerce.number().int().positive().default(3000),
  LOG_LEVEL: z.string().default("info"),

  AWS_REGION: z.string().default("us-west-2"),

  // Local/dev overrides
  DDB_ENDPOINT_URL: z.string().optional(),
  S3_ENDPOINT_URL: z.string().optional(),
  S3_PUBLIC_ENDPOINT_URL: z.string().optional(), // For pre-signed URLs accessible from browser
  SQS_ENDPOINT_URL: z.string().optional(),
  S3_FORCE_PATH_STYLE: z.string().optional(),

  // App resources
  DDB_TABLE_QUIZZES: z.string().min(1),
  DDB_TABLE_ATTEMPTS: z.string().min(1),
  DDB_TABLE_EXPORTS: z.string().min(1),
  S3_BUCKET: z.string().min(1),
  SQS_QUEUE_URL: z.string().min(1),

  // Cognito configuration
  COGNITO_USER_POOL_ID: z.string().optional(),
  COGNITO_CLIENT_ID: z.string().optional(),
  COGNITO_REGION: z.string().optional(),

  XRAY_DISABLED: z.string().optional(),
  SERVICE_NAME: z.string().default("code-quiz-api")
});

export type AppConfig = z.infer<typeof schema>;

export const config: AppConfig = schema.parse(process.env);

export const isXrayDisabled = () => boolFromEnv(config.XRAY_DISABLED);
export const isS3PathStyle = () => boolFromEnv(config.S3_FORCE_PATH_STYLE);
