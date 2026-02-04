import { PutCommand, GetCommand, UpdateCommand } from "@aws-sdk/lib-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { config } from "../config";
import { Attempt, AttemptStatus } from "../models";

export class AttemptsRepository {
  constructor(private readonly ddb: DynamoDBDocumentClient) {}

  async getAttempt(attemptId: string): Promise<Attempt | null> {
    const out = await this.ddb.send(
      new GetCommand({
        TableName: config.DDB_TABLE_ATTEMPTS,
        Key: { attemptId }
      })
    );
    return (out.Item as Attempt) ?? null;
  }

  async putAttempt(attempt: Attempt): Promise<void> {
    await this.ddb.send(
      new PutCommand({
        TableName: config.DDB_TABLE_ATTEMPTS,
        Item: attempt,
        ConditionExpression: "attribute_not_exists(attemptId)"
      })
    );
  }

  async updateAttemptStatus(params: {
    attemptId: string;
    status: AttemptStatus;
    score?: number;
    gradedAt?: string;
    errorMessage?: string;
  }): Promise<void> {
    const updates: string[] = ["#status = :status"];
    const exprNames: Record<string, string> = { "#status": "status" };
    const exprValues: Record<string, any> = { ":status": params.status };

    if (typeof params.score === "number") {
      updates.push("#score = :score");
      exprNames["#score"] = "score";
      exprValues[":score"] = params.score;
    }
    if (params.gradedAt) {
      updates.push("#gradedAt = :gradedAt");
      exprNames["#gradedAt"] = "gradedAt";
      exprValues[":gradedAt"] = params.gradedAt;
    }
    if (params.errorMessage) {
      updates.push("#errorMessage = :errorMessage");
      exprNames["#errorMessage"] = "errorMessage";
      exprValues[":errorMessage"] = params.errorMessage;
    }

    await this.ddb.send(
      new UpdateCommand({
        TableName: config.DDB_TABLE_ATTEMPTS,
        Key: { attemptId: params.attemptId },
        UpdateExpression: "SET " + updates.join(", "),
        ExpressionAttributeNames: exprNames,
        ExpressionAttributeValues: exprValues
      })
    );
  }
}
