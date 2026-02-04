import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import * as api from "./api";
import type { Quiz } from "./types";

type View =
  | { kind: "home" }
  | { kind: "takeQuiz"; quizId: string };

export default function App() {
  const [view, setView] = useState<View>({ kind: "home" });

  return (
    <div className="container">
      <header className="header">
        <h1>Code Quiz</h1>
        <nav className="nav">
          <button onClick={() => setView({ kind: "home" })}>Home</button>
        </nav>
      </header>

      {view.kind === "home" && <Home onTakeQuiz={(quizId) => setView({ kind: "takeQuiz", quizId })} />}
      {view.kind === "takeQuiz" && <TakeQuiz quizId={view.quizId} onBack={() => setView({ kind: "home" })} />}
    </div>
  );
}

function Home(props: { onTakeQuiz: (quizId: string) => void }) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<Array<Pick<Quiz, "quizId" | "title" | "createdAt">>>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await api.listQuizzes();
        setItems(res.items);
      } catch (e: any) {
        setErr(e.message ?? String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <main>
      <section className="card">
        <h2>Quizzes</h2>
        {loading && <p>Loading…</p>}
        {err && <p className="error">{err}</p>}
        {!loading && !err && items.length === 0 && <p>No quizzes yet. Create one below.</p>}
        <ul>
          {items.map((q) => (
            <li key={q.quizId} className="row">
              <span>
                <strong>{q.title}</strong>
                <small> — {new Date(q.createdAt).toLocaleString()}</small>
              </span>
              <button onClick={() => props.onTakeQuiz(q.quizId)}>Take</button>
            </li>
          ))}
        </ul>
      </section>

      <CreateQuiz onCreated={() => window.location.reload()} />
    </main>
  );
}

function CreateQuiz(props: { onCreated: () => void }) {
  const [title, setTitle] = useState("Sample quiz");
  const [prompt, setPrompt] = useState("2 + 2 = ?");
  const [choices, setChoices] = useState("3\n4\n5");
  const [answerIndex, setAnswerIndex] = useState(1);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <section className="card">
      <h2>Create quiz</h2>
      <label>
        Title
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>

      <label>
        Question prompt
        <input value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </label>

      <label>
        Choices (one per line)
        <textarea value={choices} onChange={(e) => setChoices(e.target.value)} rows={4} />
      </label>

      <label>
        Correct answer index (0-based)
        <input
          type="number"
          value={answerIndex}
          onChange={(e) => setAnswerIndex(Number(e.target.value))}
          min={0}
        />
      </label>

      <button
        disabled={busy}
        onClick={async () => {
          setMsg(null);
          setBusy(true);
          try {
            const choiceList = choices
              .split("\n")
              .map((c) => c.trim())
              .filter(Boolean);
            await api.createQuiz({
              title,
              questions: [{ prompt, choices: choiceList, answerIndex }]
            });
            setMsg("Created!");
            props.onCreated();
          } catch (e: any) {
            setMsg(e.message ?? String(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Creating…" : "Create"}
      </button>

      {msg && <p>{msg}</p>}
    </section>
  );
}

function TakeQuiz(props: { quizId: string; onBack: () => void }) {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [attemptStatus, setAttemptStatus] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [exportId, setExportId] = useState<string | null>(null);
  const [exportUrl, setExportUrl] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.getQuiz(props.quizId);
        setQuiz(res.quiz);
      } catch (e: any) {
        setErr(e.message ?? String(e));
      }
    })();
  }, [props.quizId]);

  useEffect(() => {
    if (!attemptId) return;
    const t = window.setInterval(async () => {
      const res = await api.getAttempt(attemptId);
      setAttemptStatus(res.attempt.status);
      if (res.attempt.status === "GRADED") {
        setScore(res.attempt.score ?? null);
        window.clearInterval(t);
      }
      if (res.attempt.status === "FAILED") {
        window.clearInterval(t);
      }
    }, 1500);
    return () => window.clearInterval(t);
  }, [attemptId]);

  useEffect(() => {
    if (!exportId) return;
    const t = window.setInterval(async () => {
      const res = await api.getExport(exportId);
      if (res.job.status === "COMPLETED" && res.downloadUrl) {
        setExportUrl(res.downloadUrl);
        window.clearInterval(t);
      }
      if (res.job.status === "FAILED") {
        window.clearInterval(t);
      }
    }, 1500);
    return () => window.clearInterval(t);
  }, [exportId]);

  const allAnswered = useMemo(() => {
    if (!quiz) return false;
    return quiz.questions.every((q) => typeof answers[q.questionId] === "number");
  }, [quiz, answers]);

  if (err) return <p className="error">{err}</p>;
  if (!quiz) return <p>Loading…</p>;

  return (
    <main>
      <section className="card">
        <button onClick={props.onBack}>← Back</button>
        <h2>{quiz.title}</h2>

        {quiz.questions.map((q) => (
          <div key={q.questionId} className="question">
            <p>
              <strong>{q.prompt}</strong>
            </p>
            {q.choices.map((c, idx) => (
              <label key={idx} className="choice">
                <input
                  type="radio"
                  name={q.questionId}
                  checked={answers[q.questionId] === idx}
                  onChange={() => setAnswers((a) => ({ ...a, [q.questionId]: idx }))}
                />
                {c}
              </label>
            ))}
          </div>
        ))}

        <button
          disabled={!allAnswered || !!attemptId}
          onClick={async () => {
            const payload = Object.entries(answers).map(([questionId, choiceIndex]) => ({
              questionId,
              choiceIndex
            }));
            const res = await api.submitAttempt(quiz.quizId, payload);
            setAttemptId(res.attemptId);
            setAttemptStatus(res.status);
          }}
        >
          Submit attempt
        </button>

        {attemptId && (
          <p>
            Attempt: <code>{attemptId}</code> — status: <strong>{attemptStatus}</strong>
            {score !== null && (
              <>
                {" "}
                — score: <strong>{score}</strong>
              </>
            )}
          </p>
        )}
      </section>

      <section className="card">
        <h3>Export quiz</h3>
        <button
          disabled={!!exportId}
          onClick={async () => {
            const res = await api.createExport(quiz.quizId);
            setExportId(res.exportId);
          }}
        >
          Create export
        </button>

        {exportId && (
          <p>
            Export job: <code>{exportId}</code>
          </p>
        )}
        {exportUrl && (
          <p>
            <a href={exportUrl} target="_blank" rel="noreferrer">
              Download export
            </a>
          </p>
        )}
      </section>
    </main>
  );
}
