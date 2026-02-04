import { z } from "zod";

export const jobSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("GRADE_ATTEMPT"),
    attemptId: z.string().min(1),
    quizId: z.string().min(1)
  }),
  z.object({
    type: z.literal("EXPORT_QUIZ"),
    exportId: z.string().min(1),
    quizId: z.string().min(1)
  })
]);

export type JobMessage = z.infer<typeof jobSchema>;
