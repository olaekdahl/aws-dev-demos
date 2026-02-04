import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { metricScope } from "aws-embedded-metrics";
import { config, isXrayDisabled } from "../config";
import { logger } from "../logger";
import { AttemptsRepository } from "../repositories/attempts";
import { ExportsRepository } from "../repositories/exports";
import { QuizzesRepository } from "../repositories/quizzes";
import { JobMessage } from "../jobs";
import { gradeAttempt } from "../services/grading";
import { AWSXRay } from "../observability/xray";

async function withXRaySegment<T>(name: string, fn: () => Promise<T>): Promise<T> {
  if (isXrayDisabled()) return fn();

  const SegmentCtor = (AWSXRay as any).Segment;
  const ns = AWSXRay.getNamespace();

  if (!SegmentCtor || !ns) {
    return fn();
  }

  // Run within the X-Ray namespace context so setSegment works
  return new Promise((resolve, reject) => {
    ns.run(() => {
      const segment = new SegmentCtor(name);
      AWSXRay.setSegment(segment);

      fn()
        .then((result) => {
          segment.close();
          resolve(result);
        })
        .catch((err) => {
          try {
            segment.addError?.(err);
          } catch {
            // ignore
          }
          segment.close();
          reject(err);
        });
    });
  });
}

export function createJobHandler(deps: {
  quizzesRepo: QuizzesRepository;
  attemptsRepo: AttemptsRepository;
  exportsRepo: ExportsRepository;
  s3: S3Client;
}) {
  const putMetric = metricScope((metrics) => async (name: string, value: number) => {
    metrics.setNamespace("CodeQuiz");
    metrics.putMetric(name, value, "Count");
    metrics.putDimensions({ service: "worker" });
  });

  return async (job: JobMessage) =>
    withXRaySegment(`${config.SERVICE_NAME}:${job.type}`, async () => {
      if (job.type === "GRADE_ATTEMPT") {
        const now = new Date().toISOString();
        logger.info({ job }, "Grading attempt");

        const [quiz, attempt] = await Promise.all([
          deps.quizzesRepo.getQuiz(job.quizId),
          deps.attemptsRepo.getAttempt(job.attemptId)
        ]);

        if (!quiz || !attempt) {
          logger.warn({ job }, "Quiz or attempt not found");
          await deps.attemptsRepo.updateAttemptStatus({
            attemptId: job.attemptId,
            status: "FAILED",
            gradedAt: now,
            errorMessage: "Quiz or attempt not found"
          });
          await putMetric("JobFailed", 1);
          return;
        }

        try {
          const score = gradeAttempt(quiz, attempt);
          await deps.attemptsRepo.updateAttemptStatus({
            attemptId: attempt.attemptId,
            status: "GRADED",
            score,
            gradedAt: now
          });
          await putMetric("AttemptGraded", 1);
        } catch (err: any) {
          logger.error({ err, job }, "Failed grading attempt");
          await deps.attemptsRepo.updateAttemptStatus({
            attemptId: attempt.attemptId,
            status: "FAILED",
            gradedAt: now,
            errorMessage: String(err?.message ?? err)
          });
          await putMetric("JobFailed", 1);
        }
        return;
      }

      if (job.type === "EXPORT_QUIZ") {
        const now = new Date().toISOString();
        logger.info({ job }, "Exporting quiz");

        const quiz = await deps.quizzesRepo.getQuiz(job.quizId);
        if (!quiz) {
          await deps.exportsRepo.updateExport({
            exportId: job.exportId,
            status: "FAILED",
            completedAt: now,
            errorMessage: "Quiz not found"
          });
          await putMetric("JobFailed", 1);
          return;
        }

        try {
          const key = `exports/quiz-${quiz.quizId}-${Date.now()}.json`;
          await deps.s3.send(
            new PutObjectCommand({
              Bucket: config.S3_BUCKET,
              Key: key,
              ContentType: "application/json",
              Body: JSON.stringify(quiz, null, 2)
            })
          );

          await deps.exportsRepo.updateExport({
            exportId: job.exportId,
            status: "COMPLETED",
            completedAt: now,
            s3Key: key
          });

          await putMetric("QuizExported", 1);
        } catch (err: any) {
          logger.error({ err, job }, "Failed exporting quiz");
          await deps.exportsRepo.updateExport({
            exportId: job.exportId,
            status: "FAILED",
            completedAt: now,
            errorMessage: String(err?.message ?? err)
          });
          await putMetric("JobFailed", 1);
        }
      }
    });
}
