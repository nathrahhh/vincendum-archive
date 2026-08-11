import { useEffect, useRef, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { useNavigate, useParams } from "react-router-dom";
import { request } from "../api/client";

const INVITATION_TOKEN_STORAGE_KEY = "client_invitation_token";
const DEV_ROLE_STORAGE_KEY = "credit-risk-dev-role";

type ClientInvitationAcceptResponse = {
  invitation_id: number;
  client_id: number;
  client_name: string;
  status: string;
  role: string;
};

export default function ClientInvitationPage() {
  const { token: routeToken } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const {
    isLoading,
    isAuthenticated,
    loginWithRedirect,
    getAccessTokenSilently,
  } = useAuth0();
  const [error, setError] = useState<string | null>(null);
  const [isContinuing, setIsContinuing] = useState(false);
  const [isAccepting, setIsAccepting] = useState(false);
  const acceptStartedRef = useRef(false);

  const token =
    routeToken ?? sessionStorage.getItem(INVITATION_TOKEN_STORAGE_KEY) ?? null;

  useEffect(() => {
    if (!routeToken) {
      return;
    }

    setError(null);
    sessionStorage.setItem(INVITATION_TOKEN_STORAGE_KEY, routeToken);
  }, [routeToken]);

  useEffect(() => {
    if (!isAuthenticated || isLoading || !token || acceptStartedRef.current) {
      return;
    }

    acceptStartedRef.current = true;
    let cancelled = false;

    async function acceptInvitation() {
      setIsAccepting(true);
      setError(null);

      try {
        const audience = import.meta.env.VITE_AUTH0_AUDIENCE as string | undefined;
        await getAccessTokenSilently(
          audience ? { authorizationParams: { audience } } : undefined,
        );

        const result = await request<ClientInvitationAcceptResponse>(
          "/client-invitations/accept",
          {
            method: "POST",
            body: JSON.stringify({ token }),
          },
        );

        if (cancelled) {
          return;
        }

        sessionStorage.removeItem(INVITATION_TOKEN_STORAGE_KEY);

        if (result.role === "client") {
          localStorage.setItem(DEV_ROLE_STORAGE_KEY, "client");
          navigate("/client-dashboard", { replace: true });
          return;
        }

        setError(
          `Invitation accepted for ${result.client_name}, but unexpected role: ${result.role}`,
        );
        setIsAccepting(false);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setError(
          err instanceof Error ? err.message : "Failed to accept invitation",
        );
        setIsAccepting(false);
        acceptStartedRef.current = false;
      }
    }

    void acceptInvitation();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, token, getAccessTokenSilently, navigate]);

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
          {isAccepting
            ? "Accepting your invitation…"
            : "Finishing invitation acceptance."}
        </p>
        {error ? <p className="dashboard-error">{error}</p> : null}
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
