export type QuizQuestion = {
  questionId: string;
  prompt: string;
  choices: string[];
};

export type Quiz = {
  quizId: string;
  title: string;
  questions: QuizQuestion[];
  createdAt: string;
};

export type Attempt = {
  attemptId: string;
  quizId: string;
  status: "PENDING" | "GRADED" | "FAILED";
  score?: number;
  createdAt: string;
  gradedAt?: string;
  errorMessage?: string;
};

export type ExportJob = {
  exportId: string;
  quizId: string;
  status: "PENDING" | "COMPLETED" | "FAILED";
  createdAt: string;
  completedAt?: string;
  s3Key?: string;
  errorMessage?: string;
};
