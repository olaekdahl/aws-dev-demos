import request from "supertest";
import { mockClient } from "aws-sdk-client-mock";
import { DynamoDBDocumentClient, PutCommand, ScanCommand, GetCommand } from "@aws-sdk/lib-dynamodb";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const ddbMock = mockClient(DynamoDBDocumentClient);
const sqsMock = mockClient(SQSClient);

beforeEach(() => {
  jest.resetModules();
  ddbMock.reset();
  sqsMock.reset();

  process.env.NODE_ENV = "test";
  process.env.PORT = "0";
  process.env.LOG_LEVEL = "silent";
  process.env.XRAY_DISABLED = "true";
  process.env.AWS_REGION = "us-west-2";
  process.env.DDB_TABLE_QUIZZES = "quizzes";
  process.env.DDB_TABLE_ATTEMPTS = "attempts";
  process.env.DDB_TABLE_EXPORTS = "exports";
  process.env.S3_BUCKET = "exports";
  process.env.SQS_QUEUE_URL = "http://localhost/queue";
});

test("POST /api/quizzes creates a quiz; GET /api/quizzes lists it", async () => {
  ddbMock.on(PutCommand).resolves({});
  ddbMock.on(ScanCommand).resolves({
    Items: [{ quizId: "q1", title: "My quiz", createdAt: "now" }]
  });

  const { buildApp } = await import("../src/app");
  const app = buildApp();

  const createRes = await request(app)
    .post("/api/quizzes")
    .send({
      title: "My quiz",
      questions: [
        { prompt: "2+2?", choices: ["3", "4"], answerIndex: 1 }
      ]
    });

  expect(createRes.status).toBe(201);
  expect(createRes.body.quiz.quizId).toBeDefined();

  const listRes = await request(app).get("/api/quizzes");
  expect(listRes.status).toBe(200);
  expect(listRes.body.items).toHaveLength(1);
});

test("POST /api/quizzes/:id/attempts enqueues a grading job", async () => {
  ddbMock.on(GetCommand).resolves({
    Item: {
      quizId: "q1",
      title: "Quiz",
      createdAt: "now",
      questions: [{ questionId: "qq1", prompt: "?", choices: ["a", "b"], answerIndex: 0 }]
    }
  });
  ddbMock.on(PutCommand).resolves({});
  sqsMock.on(SendMessageCommand).resolves({ MessageId: "m1" });

  const { buildApp } = await import("../src/app");
  const app = buildApp();

  const res = await request(app)
    .post("/api/quizzes/q1/attempts")
    .send({ answers: [{ questionId: "qq1", choiceIndex: 0 }] });

  expect(res.status).toBe(202);
  expect(res.body.attemptId).toBeDefined();

  expect(sqsMock.commandCalls(SendMessageCommand).length).toBe(1);
});
