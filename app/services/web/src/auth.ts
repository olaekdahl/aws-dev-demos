import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
  CognitoUserSession,
  ISignUpResult,
} from "amazon-cognito-identity-js";

export interface AuthConfig {
  enabled: boolean;
  region?: string;
  userPoolId?: string;
  clientId?: string;
}

export interface User {
  sub: string;
  email: string;
  name?: string;
  emailVerified: boolean;
}

let userPool: CognitoUserPool | null = null;
let authConfig: AuthConfig | null = null;

/**
 * Initialize auth by fetching config from the API
 */
export async function initAuth(): Promise<AuthConfig> {
  if (authConfig) return authConfig;

  try {
    const res = await fetch("/api/auth/config");
    const config: AuthConfig = await res.json();
    authConfig = config;

    if (config.enabled && config.userPoolId && config.clientId) {
      userPool = new CognitoUserPool({
        UserPoolId: config.userPoolId,
        ClientId: config.clientId,
      });
    }

    return config;
  } catch (err) {
    console.error("Failed to fetch auth config:", err);
    authConfig = { enabled: false };
    return authConfig;
  }
}

/**
 * Get current auth config
 */
export function getAuthConfig(): AuthConfig | null {
  return authConfig;
}

/**
 * Check if auth is enabled
 */
export function isAuthEnabled(): boolean {
  return authConfig?.enabled ?? false;
}

/**
 * Sign up a new user
 */
export function signUp(
  email: string,
  password: string,
  name?: string
): Promise<CognitoUser> {
  return new Promise((resolve, reject) => {
    if (!userPool) {
      return reject(new Error("Auth not initialized"));
    }

    const attributeList: CognitoUserAttribute[] = [
      new CognitoUserAttribute({ Name: "email", Value: email }),
    ];

    if (name) {
      attributeList.push(
        new CognitoUserAttribute({ Name: "name", Value: name })
      );
    }

    userPool.signUp(
      email,
      password,
      attributeList,
      [],
      (err: Error | undefined, result: ISignUpResult | undefined) => {
        if (err) {
          return reject(err);
        }
        if (result?.user) {
          resolve(result.user);
        } else {
          reject(new Error("Sign up failed"));
        }
      }
    );
  });
}

/**
 * Confirm user registration with verification code
 */
export function confirmSignUp(email: string, code: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!userPool) {
      return reject(new Error("Auth not initialized"));
    }

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.confirmRegistration(code, true, (err: Error | undefined, _result: string) => {
      if (err) {
        return reject(err);
      }
      resolve();
    });
  });
}

/**
 * Resend verification code
 */
export function resendConfirmationCode(email: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!userPool) {
      return reject(new Error("Auth not initialized"));
    }

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.resendConfirmationCode((err: Error | undefined, _result: string) => {
      if (err) {
        return reject(err);
      }
      resolve();
    });
  });
}

/**
 * Sign in an existing user
 */
export function signIn(
  email: string,
  password: string
): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    if (!userPool) {
      return reject(new Error("Auth not initialized"));
    }

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });

    cognitoUser.authenticateUser(authDetails, {
      onSuccess: (session: CognitoUserSession) => {
        resolve(session);
      },
      onFailure: (err: Error) => {
        reject(err);
      },
      newPasswordRequired: (_userAttributes: Record<string, string>) => {
        reject(new Error("New password required"));
      },
    });
  });
}

/**
 * Sign out the current user
 */
export function signOut(): void {
  if (!userPool) return;

  const cognitoUser = userPool.getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
  }
}

/**
 * Get the current authenticated user
 */
export function getCurrentUser(): Promise<User | null> {
  return new Promise((resolve) => {
    if (!userPool) {
      return resolve(null);
    }

    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      return resolve(null);
    }

    cognitoUser.getSession(
      (err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session?.isValid()) {
          return resolve(null);
        }

        cognitoUser.getUserAttributes((err: Error | undefined, attributes: CognitoUserAttribute[] | undefined) => {
          if (err) {
            return resolve(null);
          }

          const user: User = {
            sub: cognitoUser.getUsername(),
            email: "",
            emailVerified: false,
          };

          attributes?.forEach((attr: CognitoUserAttribute) => {
            switch (attr.getName()) {
              case "sub":
                user.sub = attr.getValue();
                break;
              case "email":
                user.email = attr.getValue();
                break;
              case "name":
                user.name = attr.getValue();
                break;
              case "email_verified":
                user.emailVerified = attr.getValue() === "true";
                break;
            }
          });

          resolve(user);
        });
      }
    );
  });
}

/**
 * Get the current access token
 */
export function getAccessToken(): Promise<string | null> {
  return new Promise((resolve) => {
    if (!userPool) {
      return resolve(null);
    }

    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      return resolve(null);
    }

    cognitoUser.getSession(
      (err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session?.isValid()) {
          return resolve(null);
        }

        resolve(session.getAccessToken().getJwtToken());
      }
    );
  });
}

/**
 * Get the current ID token
 */
export function getIdToken(): Promise<string | null> {
  return new Promise((resolve) => {
    if (!userPool) {
      return resolve(null);
    }

    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      return resolve(null);
    }

    cognitoUser.getSession(
      (err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session?.isValid()) {
          return resolve(null);
        }

        resolve(session.getIdToken().getJwtToken());
      }
    );
  });
}
