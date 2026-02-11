import { useEffect, useMemo, useState, useCallback } from "react";
import * as api from "./api";
import type { Quiz } from "./types";
import { useAuth } from "./AuthContext";
import { AuthModal } from "./AuthModal";
import {
  Sun,
  Moon,
  LogIn,
  LogOut,
  Plus,
  Play,
  ChevronLeft,
  Download,
  Loader2,
  CheckCircle2,
  XCircle,
  Sparkles,
  Trophy,
  Clock,
  User,
} from "lucide-react";

type View =
  | { kind: "home" }
  | { kind: "takeQuiz"; quizId: string };

export default function App() {
  const [view, setView] = useState<View>({ kind: "home" });
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("darkMode") === "true";
    }
    return false;
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, isLoading: authLoading, isAuthEnabled, signOut } = useAuth();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("darkMode", String(darkMode));
  }, [darkMode]);

  return (
    <div className="min-h-screen">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="particle w-2 h-2 top-1/4 left-1/4 animate-float" style={{ animationDelay: "0s" }} />
        <div className="particle w-3 h-3 top-1/3 right-1/4 animate-float" style={{ animationDelay: "1s" }} />
        <div className="particle w-2 h-2 bottom-1/4 left-1/3 animate-float" style={{ animationDelay: "2s" }} />
        <div className="particle w-4 h-4 top-1/2 right-1/3 animate-float" style={{ animationDelay: "0.5s" }} />
        <div className="particle w-2 h-2 bottom-1/3 right-1/5 animate-float" style={{ animationDelay: "1.5s" }} />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="glass-card mb-8 animate-fade-in-down">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setView({ kind: "home" })}
              className="flex items-center gap-3 group"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-neon group-hover:scale-110 transition-transform duration-300">
                <Sparkles className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white text-glow">Code Quiz</h1>
                <p className="text-xs text-white/50">Test your knowledge</p>
              </div>
            </button>

            <nav className="flex items-center gap-3">
              {/* Dark mode toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-3 rounded-xl glass hover:bg-white/20 transition-all duration-300"
                title={darkMode ? "Light mode" : "Dark mode"}
              >
                {darkMode ? (
                  <Sun className="text-yellow-300" size={20} />
                ) : (
                  <Moon className="text-white/80" size={20} />
                )}
              </button>

              {/* Auth button */}
              {isAuthEnabled && !authLoading && (
                user ? (
                  <div className="flex items-center gap-3">
                    <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl glass">
                      <User size={16} className="text-purple-300" />
                      <span className="text-white/80 text-sm">{user.email}</span>
                    </div>
                    <button
                      onClick={signOut}
                      className="btn-secondary flex items-center gap-2"
                    >
                      <LogOut size={18} />
                      <span className="hidden sm:inline">Sign out</span>
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowAuthModal(true)}
                    className="btn-primary flex items-center gap-2"
                  >
                    <LogIn size={18} />
                    <span>Sign in</span>
                  </button>
                )
              )}
            </nav>
          </div>
        </header>

        {/* Main content */}
        {view.kind === "home" && (
          <Home
            onTakeQuiz={(quizId) => setView({ kind: "takeQuiz", quizId })}
            onNeedAuth={() => setShowAuthModal(true)}
          />
        )}
        {view.kind === "takeQuiz" && (
          <TakeQuiz
            quizId={view.quizId}
            onBack={() => setView({ kind: "home" })}
          />
        )}

        {/* Auth modal */}
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      </div>
    </div>
  );
}

function Home(props: { onTakeQuiz: (quizId: string) => void; onNeedAuth: () => void }) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<Array<Pick<Quiz, "quizId" | "title" | "createdAt">>>([]);
  const [err, setErr] = useState<string | null>(null);
  const { user, isAuthEnabled } = useAuth();

  const refreshQuizzes = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.listQuizzes();
      setItems(res.items);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshQuizzes();
  }, [refreshQuizzes]);

  return (
    <main className="space-y-6">
      {/* Quizzes list */}
      <section className="glass-card animate-fade-in-up">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Trophy className="text-white" size={20} />
            </div>
            <h2 className="text-xl font-bold text-white">Available Quizzes</h2>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-white/10 text-white/60">
            {items.length} quiz{items.length !== 1 ? "zes" : ""}
          </span>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin text-purple-400" size={32} />
          </div>
        )}

        {err && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-200">
            <XCircle size={20} />
            <span>{err}</span>
          </div>
        )}

        {!loading && !err && items.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/5 flex items-center justify-center">
              <Sparkles className="text-white/30" size={32} />
            </div>
            <p className="text-white/50">No quizzes yet. Create one below!</p>
          </div>
        )}

        <div className="space-y-3">
          {items.map((q, idx) => (
            <div
              key={q.quizId}
              className={`flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all duration-300 animate-fade-in-up stagger-${Math.min(idx + 1, 5)}`}
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/50 to-pink-500/50 flex items-center justify-center text-white font-bold">
                  {idx + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-white">{q.title}</h3>
                  <div className="flex items-center gap-2 text-xs text-white/40">
                    <Clock size={12} />
                    <span>{new Date(q.createdAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => props.onTakeQuiz(q.quizId)}
                className="btn-primary flex items-center gap-2 py-2 px-4"
              >
                <Play size={16} />
                <span>Take Quiz</span>
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Create quiz section */}
      <CreateQuiz
        onCreated={refreshQuizzes}
        onNeedAuth={props.onNeedAuth}
        canCreate={!isAuthEnabled || !!user}
      />
    </main>
  );
}

function CreateQuiz(props: { onCreated: () => void; onNeedAuth: () => void; canCreate: boolean }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [title, setTitle] = useState("Sample quiz");
  const [prompt, setPrompt] = useState("2 + 2 = ?");
  const [choices, setChoices] = useState("3\n4\n5");
  const [answerIndex, setAnswerIndex] = useState(1);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    setBusy(true);

    try {
      const choiceList = choices
        .split("\n")
        .map((c) => c.trim())
        .filter(Boolean);

      await api.createQuiz({
        title,
        questions: [{ prompt, choices: choiceList, answerIndex }],
      });

      setMsg({ type: "success", text: "Quiz created successfully!" });
      setIsExpanded(false);
      props.onCreated();
    } catch (e: any) {
      setMsg({ type: "error", text: e.message ?? String(e) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="glass-card animate-fade-in-up stagger-2">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
            <Plus className="text-white" size={20} />
          </div>
          <h2 className="text-xl font-bold text-white">Create Quiz</h2>
        </div>

        {!props.canCreate ? (
          <button
            onClick={props.onNeedAuth}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <LogIn size={16} />
            <span>Sign in to create</span>
          </button>
        ) : (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn-secondary text-sm"
          >
            {isExpanded ? "Cancel" : "New Quiz"}
          </button>
        )}
      </div>

      {msg && (
        <div
          className={`flex items-center gap-2 p-3 mb-4 rounded-xl animate-fade-in ${
            msg.type === "success"
              ? "bg-green-500/20 border border-green-500/30 text-green-200"
              : "bg-red-500/20 border border-red-500/30 text-red-200"
          }`}
        >
          {msg.type === "success" ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
          <span className="text-sm">{msg.text}</span>
        </div>
      )}

      {isExpanded && props.canCreate && (
        <form onSubmit={handleSubmit} className="space-y-4 animate-fade-in">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Quiz Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="input-glass"
              placeholder="Enter quiz title..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Question</label>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="input-glass"
              placeholder="Enter your question..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">
              Answer Choices <span className="text-white/40">(one per line)</span>
            </label>
            <textarea
              value={choices}
              onChange={(e) => setChoices(e.target.value)}
              className="input-glass resize-none"
              rows={4}
              placeholder="Option 1&#10;Option 2&#10;Option 3"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">
              Correct Answer Index <span className="text-white/40">(0-based)</span>
            </label>
            <input
              type="number"
              value={answerIndex}
              onChange={(e) => setAnswerIndex(Number(e.target.value))}
              className="input-glass w-24"
              min={0}
              required
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {busy ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                <Plus size={18} />
                <span>Create Quiz</span>
              </>
            )}
          </button>
        </form>
      )}

      {!isExpanded && !props.canCreate && (
        <p className="text-center text-white/40 py-4">
          Sign in to create your own quizzes
        </p>
      )}
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

  if (err) {
    return (
      <div className="glass-card animate-fade-in">
        <div className="flex items-center gap-3 text-red-200">
          <XCircle size={24} />
          <span>{err}</span>
        </div>
        <button onClick={props.onBack} className="btn-secondary mt-4">
          Go back
        </button>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="glass-card animate-fade-in">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-purple-400" size={32} />
        </div>
      </div>
    );
  }

  return (
    <main className="space-y-6 animate-fade-in-up">
      {/* Quiz header */}
      <section className="glass-card">
        <button
          onClick={props.onBack}
          className="flex items-center gap-2 text-white/60 hover:text-white mb-4 transition-colors"
        >
          <ChevronLeft size={20} />
          <span>Back to quizzes</span>
        </button>

        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Sparkles className="text-white" size={28} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{quiz.title}</h2>
            <p className="text-white/50">{quiz.questions.length} question{quiz.questions.length !== 1 ? "s" : ""}</p>
          </div>
        </div>
      </section>

      {/* Questions */}
      <section className="glass-card">
        <div className="space-y-8">
          {quiz.questions.map((q, qIdx) => (
            <div key={q.questionId} className={`animate-fade-in-up stagger-${Math.min(qIdx + 1, 5)}`}>
              <div className="flex items-start gap-4 mb-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-500/30 flex items-center justify-center text-purple-300 font-bold text-sm">
                  {qIdx + 1}
                </span>
                <p className="text-lg font-medium text-white">{q.prompt}</p>
              </div>

              <div className="space-y-2 ml-12">
                {q.choices.map((choice, idx) => {
                  const isSelected = answers[q.questionId] === idx;
                  return (
                    <label
                      key={idx}
                      className={`radio-glass ${isSelected ? "selected" : ""}`}
                    >
                      <div className={`radio-dot ${isSelected ? "checked" : ""}`} />
                      <input
                        type="radio"
                        name={q.questionId}
                        checked={isSelected}
                        onChange={() => setAnswers((a) => ({ ...a, [q.questionId]: idx }))}
                        className="sr-only"
                      />
                      <span className="text-white/80">{choice}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Submit button */}
        <div className="mt-8 pt-6 border-t border-white/10">
          <button
            disabled={!allAnswered || !!attemptId}
            onClick={async () => {
              const payload = Object.entries(answers).map(([questionId, choiceIndex]) => ({
                questionId,
                choiceIndex,
              }));
              const res = await api.submitAttempt(quiz.quizId, payload);
              setAttemptId(res.attemptId);
              setAttemptStatus(res.status);
            }}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <CheckCircle2 size={20} />
            <span>Submit Answers</span>
          </button>
        </div>

        {/* Result display */}
        {attemptId && (
          <div className="mt-6 p-4 rounded-xl bg-white/5 border border-white/10 animate-fade-in">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/60 text-sm">Attempt ID</p>
                <code className="text-purple-300 text-sm">{attemptId}</code>
              </div>
              <div className="text-right">
                <p className="text-white/60 text-sm">Status</p>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    attemptStatus === "GRADED"
                      ? "bg-green-500/20 text-green-300"
                      : attemptStatus === "FAILED"
                      ? "bg-red-500/20 text-red-300"
                      : "bg-yellow-500/20 text-yellow-300"
                  }`}
                >
                  {attemptStatus === "PENDING" && <Loader2 className="animate-spin" size={12} />}
                  {attemptStatus}
                </span>
              </div>
            </div>

            {score !== null && (
              <div className="mt-4 pt-4 border-t border-white/10 text-center">
                <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                  <Trophy className="text-yellow-400" size={24} />
                  <span className="text-2xl font-bold text-white">Score: {score}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Export section */}
      <section className="glass-card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
            <Download className="text-white" size={20} />
          </div>
          <h3 className="text-lg font-bold text-white">Export Quiz</h3>
        </div>

        <button
          disabled={!!exportId}
          onClick={async () => {
            const res = await api.createExport(quiz.quizId);
            setExportId(res.exportId);
          }}
          className="btn-secondary flex items-center gap-2"
        >
          {exportId && !exportUrl ? (
            <Loader2 className="animate-spin" size={18} />
          ) : (
            <Download size={18} />
          )}
          <span>{exportId ? "Exporting..." : "Create Export"}</span>
        </button>

        {exportId && (
          <p className="mt-3 text-sm text-white/50">
            Export ID: <code className="text-purple-300">{exportId}</code>
          </p>
        )}

        {exportUrl && (
          <a
            href={exportUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 mt-3 text-purple-300 hover:text-purple-200 transition-colors"
          >
            <Download size={16} />
            Download export file
          </a>
        )}
      </section>
    </main>
  );
}
