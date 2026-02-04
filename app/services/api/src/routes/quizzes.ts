import { Router } from "express";
import { z } from "zod";
import { v4 as uuidv4 } from "uuid";
import { QuizzesRepository } from "../repositories/quizzes";
import { AttemptsRepository } from "../repositories/attempts";
import { ExportsRepository } from "../repositories/exports";
import { JobsQueue } from "../aws/jobsQueue";
import { Quiz } from "../models";
import { putCountMetric } from "../observability/metrics";

const createQuizSchema = z.object({
  title: z.string().min(3).max(120),
  questions: z
    .array(
      z.object({
        prompt: z.string().min(1).max(500),
        choices: z.array(z.string().min(1).max(200)).min(2).max(8),
        answerIndex: z.number().int().min(0)
      })
    )
    .min(1)
    .max(50)
});

const createAttemptSchema = z.object({
  answers: z
    .array(
      z.object({
        questionId: z.string().min(1),
        choiceIndex: z.number().int().min(0)
      })
    )
    .min(1)
});

export function quizzesRoutes(deps: {
  quizzesRepo: QuizzesRepository;
  attemptsRepo: AttemptsRepository;
  exportsRepo: ExportsRepository;
  jobs: JobsQueue;
}) {
  const router = Router();

  router.get("/", async (_req, res) => {
    const items = await deps.quizzesRepo.listQuizzes();
    res.json({ items });
  });

  router.post("/", async (req, res) => {
    const body = createQuizSchema.parse(req.body);
    const now = new Date().toISOString();

    const quiz: Quiz = {
      quizId: uuidv4(),
      title: body.title,
      questions: body.questions.map((q, idx) => ({
        questionId: uuidv4(),
        prompt: q.prompt,
        choices: q.choices,
        answerIndex: Math.min(q.answerIndex, q.choices.length - 1)
      })),
      createdAt: now
    };

    await deps.quizzesRepo.putQuiz(quiz);
    await putCountMetric("QuizCreated", 1);
    res.status(201).json({ quiz });
  });

  router.get("/:quizId", async (req, res) => {
    const quiz = await deps.quizzesRepo.getQuiz(req.params.quizId);
    if (!quiz) return res.status(404).json({ message: "Quiz not found" });
    res.json({ quiz });
  });

  router.post("/:quizId/attempts", async (req, res) => {
    const quiz = await deps.quizzesRepo.getQuiz(req.params.quizId);
    if (!quiz) return res.status(404).json({ message: "Quiz not found" });

    const body = createAttemptSchema.parse(req.body);

    const now = new Date().toISOString();
    const attemptId = uuidv4();

    await deps.attemptsRepo.putAttempt({
      attemptId,
      quizId: quiz.quizId,
      answers: body.answers,
      status: "PENDING",
      createdAt: now
    });

    await deps.jobs.send({ type: "GRADE_ATTEMPT", attemptId, quizId: quiz.quizId });
    await putCountMetric("AttemptSubmitted", 1);

    res.status(202).json({ attemptId, status: "PENDING" });
  });

  router.post("/:quizId/exports", async (req, res) => {
    const quiz = await deps.quizzesRepo.getQuiz(req.params.quizId);
    if (!quiz) return res.status(404).json({ message: "Quiz not found" });

    const exportId = uuidv4();
    const now = new Date().toISOString();

    await deps.exportsRepo.putExport({
      exportId,
      quizId: quiz.quizId,
      status: "PENDING",
      createdAt: now
    });

    await deps.jobs.send({ type: "EXPORT_QUIZ", exportId, quizId: quiz.quizId });
    await putCountMetric("ExportRequested", 1);

    res.status(202).json({ exportId, status: "PENDING" });
  });

  return router;
}
