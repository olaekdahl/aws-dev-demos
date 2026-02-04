import { SendMessageCommand, SQSClient } from "@aws-sdk/client-sqs";
import { config } from "../config";

export type JobMessage =
  | { type: "GRADE_ATTEMPT"; attemptId: string; quizId: string }
  | { type: "EXPORT_QUIZ"; exportId: string; quizId: string };

export class JobsQueue {
  constructor(private readonly sqs: SQSClient) {}

  async send(message: JobMessage) {
    await this.sqs.send(
      new SendMessageCommand({
        QueueUrl: config.SQS_QUEUE_URL,
        MessageBody: JSON.stringify(message)
      })
    );
  }
}
