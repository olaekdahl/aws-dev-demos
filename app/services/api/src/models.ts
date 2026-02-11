export type QuizQuestion = {
  questionId: string;
  prompt: string;
  choices: string[];
  answerIndex: number;
};

export type Quiz = {
  quizId: string;
  title: string;
  questions: QuizQuestion[];
  createdAt: string;
  createdBy?: string;
};

export type AttemptAnswer = {
  questionId: string;
  choiceIndex: number;
};

export type AttemptStatus = "PENDING" | "GRADED" | "FAILED";

export type Attempt = {
  attemptId: string;
  quizId: string;
  answers: AttemptAnswer[];
  status: AttemptStatus;
  score?: number;
  createdAt: string;
  gradedAt?: string;
  errorMessage?: string;
};

export type ExportStatus = "PENDING" | "COMPLETED" | "FAILED";

export type ExportJob = {
  exportId: string;
  quizId: string;
  status: ExportStatus;
  createdAt: string;
  completedAt?: string;
  s3Key?: string;
  errorMessage?: string;
};
