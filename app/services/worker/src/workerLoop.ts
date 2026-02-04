import { ReceiveMessageCommand, DeleteMessageCommand, SQSClient } from "@aws-sdk/client-sqs";
import { config } from "./config";
import { logger } from "./logger";
import { jobSchema } from "./jobs";

export async function runWorkerLoop(deps: {
  sqs: SQSClient;
  handleJob: (job: any) => Promise<void>;
}) {
  logger.info("Worker loop started");

  while (true) {
    try {
      const resp = await deps.sqs.send(
        new ReceiveMessageCommand({
          QueueUrl: config.SQS_QUEUE_URL,
          MaxNumberOfMessages: config.WORKER_MAX_MESSAGES,
          WaitTimeSeconds: 20
        })
      );

      const messages = resp.Messages ?? [];
      if (messages.length === 0) continue;

      for (const m of messages) {
        if (!m.Body || !m.ReceiptHandle) continue;

        let job: any;
        try {
          job = jobSchema.parse(JSON.parse(m.Body));
        } catch (err) {
          logger.warn({ err, body: m.Body }, "Invalid message body; deleting");
          await deps.sqs.send(
            new DeleteMessageCommand({
              QueueUrl: config.SQS_QUEUE_URL,
              ReceiptHandle: m.ReceiptHandle
            })
          );
          continue;
        }

        await deps.handleJob(job);

        await deps.sqs.send(
          new DeleteMessageCommand({
            QueueUrl: config.SQS_QUEUE_URL,
            ReceiptHandle: m.ReceiptHandle
          })
        );
      }
    } catch (err) {
      logger.error({ err }, "Worker loop error");
      await new Promise((r) => setTimeout(r, config.WORKER_POLL_INTERVAL_MS));
    }
  }
}
