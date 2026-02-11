import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import * as auth from "./auth";

interface AuthContextType {
  user: auth.User | null;
  isLoading: boolean;
  isAuthEnabled: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  confirmSignUp: (email: string, code: string) => Promise<void>;
  resendCode: (email: string) => Promise<void>;
  signOut: () => void;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<auth.User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthEnabled, setIsAuthEnabled] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const config = await auth.initAuth();
        setIsAuthEnabled(config.enabled);

        if (config.enabled) {
          const currentUser = await auth.getCurrentUser();
          setUser(currentUser);
        }
      } catch (err) {
        console.error("Auth init error:", err);
      } finally {
        setIsLoading(false);
      }
    }

    init();
  }, []);

  const handleSignIn = useCallback(
    async (email: string, password: string) => {
      await auth.signIn(email, password);
      const user = await auth.getCurrentUser();
      setUser(user);
    },
    []
  );

  const handleSignUp = useCallback(
    async (email: string, password: string, name?: string) => {
      await auth.signUp(email, password, name);
    },
    []
  );

  const handleConfirmSignUp = useCallback(
    async (email: string, code: string) => {
      await auth.confirmSignUp(email, code);
    },
    []
  );

  const handleResendCode = useCallback(async (email: string) => {
    await auth.resendConfirmationCode(email);
  }, []);

  const handleSignOut = useCallback(() => {
    auth.signOut();
    setUser(null);
  }, []);

  const getToken = useCallback(async () => {
    return auth.getAccessToken();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthEnabled,
        signIn: handleSignIn,
        signUp: handleSignUp,
        confirmSignUp: handleConfirmSignUp,
        resendCode: handleResendCode,
        signOut: handleSignOut,
        getToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
