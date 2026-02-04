import { NextFunction, Request, Response } from "express";
import { ZodError } from "zod";
import { logger } from "../logger";

export function errorHandler(err: unknown, _req: Request, res: Response, _next: NextFunction) {
  if (err instanceof ZodError) {
    return res.status(400).json({
      message: "Invalid request",
      issues: err.issues
    });
  }

  logger.error({ err }, "Unhandled error");
  res.status(500).json({ message: "Internal server error" });
}
