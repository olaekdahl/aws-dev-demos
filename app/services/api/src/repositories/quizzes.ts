import { PutCommand, ScanCommand, GetCommand } from "@aws-sdk/lib-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";
import { config } from "../config";
import { Quiz } from "../models";

export class QuizzesRepository {
  constructor(private readonly ddb: DynamoDBDocumentClient) {}

  async listQuizzes(): Promise<Pick<Quiz, "quizId" | "title" | "createdAt">[]> {
    const out = await this.ddb.send(
      new ScanCommand({
        TableName: config.DDB_TABLE_QUIZZES,
        ProjectionExpression: "quizId, title, createdAt"
      })
    );
    return (out.Items as any[])?.map((i) => ({
      quizId: i.quizId,
      title: i.title,
      createdAt: i.createdAt
    })) ?? [];
  }

  async getQuiz(quizId: string): Promise<Quiz | null> {
    const out = await this.ddb.send(
      new GetCommand({
        TableName: config.DDB_TABLE_QUIZZES,
        Key: { quizId }
      })
    );
    return (out.Item as Quiz) ?? null;
  }

  async putQuiz(quiz: Quiz): Promise<void> {
    await this.ddb.send(
      new PutCommand({
        TableName: config.DDB_TABLE_QUIZZES,
        Item: quiz,
        ConditionExpression: "attribute_not_exists(quizId)"
      })
    );
  }
}
