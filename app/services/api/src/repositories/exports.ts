import { PutCommand, GetCommand, UpdateCommand } from "@aws-sdk/lib-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { config } from "../config";
import { ExportJob, ExportStatus } from "../models";

export class ExportsRepository {
  constructor(private readonly ddb: DynamoDBDocumentClient) {}

  async getExport(exportId: string): Promise<ExportJob | null> {
    const out = await this.ddb.send(
      new GetCommand({
        TableName: config.DDB_TABLE_EXPORTS,
        Key: { exportId }
      })
    );
    return (out.Item as ExportJob) ?? null;
  }

  async putExport(job: ExportJob): Promise<void> {
    await this.ddb.send(
      new PutCommand({
        TableName: config.DDB_TABLE_EXPORTS,
        Item: job,
        ConditionExpression: "attribute_not_exists(exportId)"
      })
    );
  }

  async updateExport(params: {
    exportId: string;
    status: ExportStatus;
    completedAt?: string;
    s3Key?: string;
    errorMessage?: string;
  }): Promise<void> {
    const updates: string[] = ["#status = :status"];
    const exprNames: Record<string, string> = { "#status": "status" };
    const exprValues: Record<string, any> = { ":status": params.status };

    if (params.completedAt) {
      updates.push("#completedAt = :completedAt");
      exprNames["#completedAt"] = "completedAt";
      exprValues[":completedAt"] = params.completedAt;
    }
    if (params.s3Key) {
      updates.push("#s3Key = :s3Key");
      exprNames["#s3Key"] = "s3Key";
      exprValues[":s3Key"] = params.s3Key;
    }
    if (params.errorMessage) {
      updates.push("#errorMessage = :errorMessage");
      exprNames["#errorMessage"] = "errorMessage";
      exprValues[":errorMessage"] = params.errorMessage;
    }

    await this.ddb.send(
      new UpdateCommand({
        TableName: config.DDB_TABLE_EXPORTS,
        Key: { exportId: params.exportId },
        UpdateExpression: "SET " + updates.join(", "),
        ExpressionAttributeNames: exprNames,
        ExpressionAttributeValues: exprValues
      })
    );
  }
}
