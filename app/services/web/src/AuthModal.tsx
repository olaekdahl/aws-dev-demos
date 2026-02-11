import { useState } from "react";
import { useAuth } from "./AuthContext";
import { X, Mail, Lock, User, Loader2, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";

type AuthView = "signIn" | "signUp" | "confirmCode";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialView?: AuthView;
}

export function AuthModal({ isOpen, onClose, initialView = "signIn" }: AuthModalProps) {
  const { signIn, signUp, confirmSignUp, resendCode } = useAuth();
  const [view, setView] = useState<AuthView>(initialView);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await signIn(email, password);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await signUp(email, password, name || undefined);
      setSuccess("Check your email for a verification code!");
      setView("confirmCode");
    } catch (err: any) {
      setError(err.message || "Failed to sign up");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await confirmSignUp(email, code);
      setSuccess("Email verified! You can now sign in.");
      setView("signIn");
    } catch (err: any) {
      setError(err.message || "Failed to verify code");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      await resendCode(email);
      setSuccess("Verification code resent to your email!");
    } catch (err: any) {
      setError(err.message || "Failed to resend code");
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setError(null);
    setSuccess(null);
    setIsLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md animate-scale-in">
        <div className="glass-card gradient-border">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full text-white/60 hover:text-white hover:bg-white/10 transition-all duration-200"
          >
            <X size={20} />
          </button>

          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              {view === "signIn" && "Welcome Back"}
              {view === "signUp" && "Create Account"}
              {view === "confirmCode" && "Verify Email"}
            </h2>
            <p className="text-white/60 text-sm">
              {view === "signIn" && "Sign in to create quizzes"}
              {view === "signUp" && "Join to start creating quizzes"}
              {view === "confirmCode" && "Enter the code sent to your email"}
            </p>
          </div>

          {/* Messages */}
          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-200 animate-fade-in">
              <AlertCircle size={18} />
              <span className="text-sm">{error}</span>
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 p-3 mb-4 rounded-xl bg-green-500/20 border border-green-500/30 text-green-200 animate-fade-in">
              <CheckCircle2 size={18} />
              <span className="text-sm">{success}</span>
            </div>
          )}

          {/* Sign In Form */}
          {view === "signIn" && (
            <form onSubmit={handleSignIn} className="space-y-4">
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-12"
                  required
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-glass pl-12"
                  required
                  minLength={8}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>

              <p className="text-center text-white/60 text-sm">
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setView("signUp");
                    resetForm();
                  }}
                  className="text-purple-300 hover:text-purple-200 font-medium transition-colors"
                >
                  Sign up
                </button>
              </p>
            </form>
          )}

          {/* Sign Up Form */}
          {view === "signUp" && (
            <form onSubmit={handleSignUp} className="space-y-4">
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                <input
                  type="text"
                  placeholder="Name (optional)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-glass pl-12"
                />
              </div>

              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-glass pl-12"
                  required
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={18} />
                <input
                  type="password"
                  placeholder="Password (min 8 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-glass pl-12"
                  required
                  minLength={8}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <>
                    <span>Create Account</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>

              <p className="text-center text-white/60 text-sm">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setView("signIn");
                    resetForm();
                  }}
                  className="text-purple-300 hover:text-purple-200 font-medium transition-colors"
                >
                  Sign in
                </button>
              </p>
            </form>
          )}

          {/* Confirm Code Form */}
          {view === "confirmCode" && (
            <form onSubmit={handleConfirmCode} className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Verification code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="input-glass text-center text-2xl tracking-widest"
                  required
                  maxLength={6}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <>
                    <span>Verify Email</span>
                    <CheckCircle2 size={18} />
                  </>
                )}
              </button>

              <p className="text-center text-white/60 text-sm">
                Didn't receive a code?{" "}
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={isLoading}
                  className="text-purple-300 hover:text-purple-200 font-medium transition-colors"
                >
                  Resend code
                </button>
              </p>

              <p className="text-center text-white/60 text-sm">
                <button
                  type="button"
                  onClick={() => {
                    setView("signIn");
                    resetForm();
                  }}
                  className="text-purple-300 hover:text-purple-200 font-medium transition-colors"
                >
                  Back to sign in
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
