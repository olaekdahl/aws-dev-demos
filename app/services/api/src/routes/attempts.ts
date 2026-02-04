import { Router } from "express";
import { AttemptsRepository } from "../repositories/attempts";

export function attemptsRoutes(deps: { attemptsRepo: AttemptsRepository }) {
  const router = Router();

  router.get("/:attemptId", async (req, res) => {
    const attempt = await deps.attemptsRepo.getAttempt(req.params.attemptId);
    if (!attempt) return res.status(404).json({ message: "Attempt not found" });
    res.json({ attempt });
  });

  return router;
}
