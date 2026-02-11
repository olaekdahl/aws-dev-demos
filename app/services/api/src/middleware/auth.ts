import { Request, Response, NextFunction } from "express";
import { createRemoteJWKSet, jwtVerify, JWTPayload } from "jose";
import { config } from "../config";
import { logger } from "../logger";

// Extend Express Request to include user info
declare global {
  namespace Express {
    interface Request {
      user?: CognitoUser;
    }
  }
}

export interface CognitoUser {
  sub: string;
  email?: string;
  name?: string;
  emailVerified?: boolean;
}

// Cache the JWKS for performance
let jwks: ReturnType<typeof createRemoteJWKSet> | null = null;

function getJWKS() {
  if (!jwks && config.COGNITO_USER_POOL_ID && config.COGNITO_REGION) {
    const region = config.COGNITO_REGION;
    const userPoolId = config.COGNITO_USER_POOL_ID;
    const jwksUri = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}/.well-known/jwks.json`;
    jwks = createRemoteJWKSet(new URL(jwksUri));
  }
  return jwks;
}

/**
 * Validates a Cognito JWT token and extracts user information.
 */
async function validateToken(token: string): Promise<CognitoUser | null> {
  const jwksSet = getJWKS();
  if (!jwksSet) {
    logger.warn("Cognito not configured, skipping token validation");
    return null;
  }

  try {
    const region = config.COGNITO_REGION!;
    const userPoolId = config.COGNITO_USER_POOL_ID!;
    const clientId = config.COGNITO_CLIENT_ID!;
    const issuer = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`;

    const { payload } = await jwtVerify(token, jwksSet, {
      issuer,
      audience: clientId,
    });

    // For access tokens, audience might not be set, so verify token_use
    const tokenUse = (payload as JWTPayload & { token_use?: string }).token_use;
    if (tokenUse !== "access" && tokenUse !== "id") {
      logger.warn({ tokenUse }, "Invalid token_use claim");
      return null;
    }

    return {
      sub: payload.sub!,
      email: (payload as any).email,
      name: (payload as any).name,
      emailVerified: (payload as any).email_verified,
    };
  } catch (err) {
    logger.warn({ err }, "Token validation failed");
    return null;
  }
}

/**
 * Optional authentication middleware - attaches user to request if valid token present.
 * Does NOT reject requests without valid tokens.
 */
export function optionalAuth(req: Request, _res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  
  if (!authHeader?.startsWith("Bearer ")) {
    return next();
  }

  const token = authHeader.slice(7);
  
  validateToken(token)
    .then((user) => {
      if (user) {
        req.user = user;
      }
      next();
    })
    .catch((err) => {
      logger.error({ err }, "Error in optional auth middleware");
      next();
    });
}

/**
 * Required authentication middleware - rejects requests without valid tokens.
 */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith("Bearer ")) {
    return res.status(401).json({ 
      error: "Unauthorized", 
      message: "Missing or invalid Authorization header" 
    });
  }

  const token = authHeader.slice(7);

  validateToken(token)
    .then((user) => {
      if (!user) {
        return res.status(401).json({ 
          error: "Unauthorized", 
          message: "Invalid or expired token" 
        });
      }
      req.user = user;
      next();
    })
    .catch((err) => {
      logger.error({ err }, "Error in require auth middleware");
      res.status(500).json({ error: "Internal server error" });
    });
}

/**
 * Check if Cognito is configured
 */
export function isCognitoConfigured(): boolean {
  return !!(config.COGNITO_USER_POOL_ID && config.COGNITO_CLIENT_ID && config.COGNITO_REGION);
}
