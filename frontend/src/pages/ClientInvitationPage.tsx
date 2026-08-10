import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate, useParams } from "react-router-dom";

const INVITATION_TOKEN_STORAGE_KEY = "client_invitation_token";

export default function ClientInvitationPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isLoading, isAuthenticated, loginWithRedirect } = useAuth0();
  const [error, setError] = useState<string | null>(null);
  const [isContinuing, setIsContinuing] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invitation token is missing.");
      return;
    }

    setError(null);
    sessionStorage.setItem(INVITATION_TOKEN_STORAGE_KEY, token);
  }, [token]);

  async function handleContinueWithAuth0() {
    if (!token) {
      setError("Invitation token is missing.");
      return;
    }

    setIsContinuing(true);
    setError(null);
    sessionStorage.setItem(INVITATION_TOKEN_STORAGE_KEY, token);

    try {
      await loginWithRedirect({
        appState: {
          returnTo: `/invite/${token}`,
        },
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start Auth0 login",
      );
      setIsContinuing(false);
    }
  }

  if (isLoading) {
    return <div>Loading authentication...</div>;
  }

  if (!token) {
    return (
      <div className="deal-form">
        <h1 className="deal-form__title">Client invitation</h1>
        <p className="dashboard-error">Invitation token is missing.</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="deal-form">
        <h1 className="deal-form__title">Client invitation</h1>
        <p className="deal-form__subtitle">
          You are signed in. Your invitation is ready for the next step.
          Acceptance is not available yet because the backend endpoint has not
          been implemented.
        </p>
        {error ? <p className="dashboard-error">{error}</p> : null}
        <button
          className="deal-form__submit"
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          Go to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="deal-form">
      <h1 className="deal-form__title">Client invitation</h1>
      <p className="deal-form__subtitle">
        You have been invited to access a client on this platform. Continue with
        Auth0 to accept the invitation.
      </p>

      {error ? <p className="dashboard-error">{error}</p> : null}

      <button
        className="deal-form__submit"
        type="button"
        disabled={isContinuing}
        onClick={handleContinueWithAuth0}
      >
        {isContinuing ? "Redirecting…" : "Continue with Auth0"}
      </button>
    </div>
  );
}

export { INVITATION_TOKEN_STORAGE_KEY };
