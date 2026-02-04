import { Attempt, Quiz } from "../models";

export function gradeAttempt(quiz: Quiz, attempt: Attempt): number {
  const answerMap = new Map(attempt.answers.map((a) => [a.questionId, a.choiceIndex]));
  const total = quiz.questions.length;

  if (total === 0) return 0;

  let correct = 0;
  for (const q of quiz.questions) {
    const chosen = answerMap.get(q.questionId);
    if (chosen === q.answerIndex) correct++;
  }

  // score as 0..100 integer
  return Math.round((correct / total) * 100);
}
