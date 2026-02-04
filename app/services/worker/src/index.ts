import { initXRay } from "./observability/xray";
import { createDynamoDocClient, createS3Client, createSqsClient } from "./aws/clients";
import { QuizzesRepository } from "./repositories/quizzes";
import { AttemptsRepository } from "./repositories/attempts";
import { ExportsRepository } from "./repositories/exports";
import { createJobHandler } from "./handlers/jobHandler";
import { runWorkerLoop } from "./workerLoop";

initXRay();

const ddb = createDynamoDocClient();
const s3 = createS3Client();
const sqs = createSqsClient();

const quizzesRepo = new QuizzesRepository(ddb);
const attemptsRepo = new AttemptsRepository(ddb);
const exportsRepo = new ExportsRepository(ddb);

const handleJob = createJobHandler({ quizzesRepo, attemptsRepo, exportsRepo, s3 });

runWorkerLoop({ sqs, handleJob }).catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});
