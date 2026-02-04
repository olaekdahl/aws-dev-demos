import { GetCommand } from "@aws-sdk/lib-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { config } from "../config";
import { Quiz } from "../models";

export class QuizzesRepository {
  constructor(private readonly ddb: DynamoDBDocumentClient) {}

  async getQuiz(quizId: string): Promise<Quiz | null> {
    const out = await this.ddb.send(
      new GetCommand({
        TableName: config.DDB_TABLE_QUIZZES,
        Key: { quizId }
      })
    );
    return (out.Item as Quiz) ?? null;
  }
}
