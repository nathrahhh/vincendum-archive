import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getCurrentUser } from "../services/authService";
import type { CurrentUser } from "../types/auth";

export type AppRole = "admin" | "client";

type CurrentUserContextValue = {
  user: CurrentUser | null;
  role: AppRole;
  isLoading: boolean;
  error: string | null;
  refreshUser: () => Promise<CurrentUser>;
};

const CurrentUserContext = createContext<CurrentUserContextValue | null>(null);

function normalizeRole(role: string): AppRole {
  return role === "client" ? "client" : "admin";
}

export function defaultPathForRole(role: AppRole): string {
  return role === "client" ? "/client" : "/dashboard";
}

export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    const next = await getCurrentUser();
    setUser(next);
    setError(null);
    return next;
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const next = await getCurrentUser();
        if (!cancelled) {
          setUser(next);
        }
      } catch (err) {
        if (!cancelled) {
          setUser(null);
          setError(
            err instanceof Error ? err.message : "Failed to load current user",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<CurrentUserContextValue>(
    () => ({
      user,
      role: normalizeRole(user?.role ?? "admin"),
      isLoading,
      error,
      refreshUser,
    }),
    [user, isLoading, error, refreshUser],
  );

  return (
    <CurrentUserContext.Provider value={value}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUser(): CurrentUserContextValue {
  const context = useContext(CurrentUserContext);
  if (!context) {
    throw new Error("useCurrentUser must be used within CurrentUserProvider");
  }
  return context;
}
