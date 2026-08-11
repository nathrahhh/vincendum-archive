import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type DevRole = "client" | "admin";

const STORAGE_KEY = "credit-risk-dev-role";

function readStoredRole(): DevRole {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "client" || stored === "admin" ? stored : "admin";
}

type DevRoleContextValue = {
  role: DevRole;
  setRole: (role: DevRole) => void;
};

const DevRoleContext = createContext<DevRoleContextValue | null>(null);

export function DevRoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<DevRole>(readStoredRole);

  const setRole = useCallback((next: DevRole) => {
    localStorage.setItem(STORAGE_KEY, next);
    setRoleState(next);
  }, []);

  const value = useMemo(() => ({ role, setRole }), [role, setRole]);

  return <DevRoleContext.Provider value={value}>{children}</DevRoleContext.Provider>;
}

export function useDevRole(): DevRoleContextValue {
  const context = useContext(DevRoleContext);
  if (!context) {
    throw new Error("useDevRole must be used within DevRoleProvider");
  }
  return context;
}

export function defaultPathForRole(role: DevRole): string {
  return role === "client" ? "/client-dashboard" : "/dashboard";
}
