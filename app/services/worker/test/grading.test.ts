import { gradeAttempt } from "../src/services/grading";
import { Attempt, Quiz } from "../src/models";

test("gradeAttempt computes percentage score", () => {
  const quiz: Quiz = {
    quizId: "q1",
    title: "Quiz",
    createdAt: "now",
    questions: [
      { questionId: "a", prompt: "1", choices: ["x", "y"], answerIndex: 0 },
      { questionId: "b", prompt: "2", choices: ["x", "y"], answerIndex: 1 }
    ]
  };

  const attempt: Attempt = {
    attemptId: "t1",
    quizId: "q1",
    createdAt: "now",
    status: "PENDING",
    answers: [
      { questionId: "a", choiceIndex: 0 },
      { questionId: "b", choiceIndex: 0 }
    ]
  };

  expect(gradeAttempt(quiz, attempt)).toBe(50);
});
