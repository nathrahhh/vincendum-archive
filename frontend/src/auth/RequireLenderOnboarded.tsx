import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useCurrentUser } from "./CurrentUserProvider";

type RequireLenderOnboardedProps = {
  children: ReactNode;
};

/**
 * After Auth0 login, send first-time admins (no lender_id) to /onboarding.
 * Clients skip lender onboarding entirely.
 */
export default function RequireLenderOnboarded({
  children,
}: RequireLenderOnboardedProps) {
  const { user, isLoading, error } = useCurrentUser();

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  if (isLoading || !user) {
    return <div>Loading account...</div>;
  }

  if (user.role === "client") {
    return <>{children}</>;
  }

  if (user.role === "admin" && user.lender_id === null) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}
