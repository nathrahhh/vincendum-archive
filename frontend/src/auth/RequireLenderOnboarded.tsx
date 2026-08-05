import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { getCurrentUser } from "../services/authService";

type RequireLenderOnboardedProps = {
  children: ReactNode;
};

/**
 * After Auth0 login, send first-time admins (no lender_id) to /onboarding.
 */
export default function RequireLenderOnboarded({
  children,
}: RequireLenderOnboardedProps) {
  const [status, setStatus] = useState<"loading" | "needs_onboarding" | "ready">(
    "loading",
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      try {
        const user = await getCurrentUser();
        if (cancelled) {
          return;
        }
        setStatus(user.lender_id === null ? "needs_onboarding" : "ready");
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load current user",
          );
          setStatus("loading");
        }
      }
    }

    loadUser();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  if (status === "loading") {
    return <div>Loading account...</div>;
  }

  if (status === "needs_onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}
