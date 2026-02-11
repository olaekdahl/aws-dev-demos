import type { Attempt, ExportJob, Quiz } from "./types";
import { getAccessToken } from "./auth";

async function http<T>(path: string, options?: RequestInit & { auth?: boolean }): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };

  // Add auth token if requested
  if (options?.auth) {
    const token = await getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(path, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function listQuizzes(): Promise<{ items: Array<Pick<Quiz, "quizId" | "title" | "createdAt">> }> {
  return http("/api/quizzes");
}

export async function createQuiz(input: {
  title: string;
  questions: Array<{ prompt: string; choices: string[]; answerIndex: number }>;
}): Promise<{ quiz: Quiz }> {
  return http("/api/quizzes", { method: "POST", body: JSON.stringify(input), auth: true });
}

export async function getQuiz(quizId: string): Promise<{ quiz: Quiz }> {
  return http(`/api/quizzes/${quizId}`);
}

export async function submitAttempt(quizId: string, answers: Array<{ questionId: string; choiceIndex: number }>) {
  return http<{ attemptId: string; status: string }>(`/api/quizzes/${quizId}/attempts`, {
    method: "POST",
    body: JSON.stringify({ answers })
  });
}

export async function getAttempt(attemptId: string): Promise<{ attempt: Attempt }> {
  return http(`/api/attempts/${attemptId}`);
}

export async function createExport(quizId: string): Promise<{ exportId: string; status: string }> {
  return http(`/api/quizzes/${quizId}/exports`, { method: "POST", body: JSON.stringify({}) });
}

export async function getExport(exportId: string): Promise<{ job: ExportJob; downloadUrl?: string }> {
  return http(`/api/exports/${exportId}`);
}
