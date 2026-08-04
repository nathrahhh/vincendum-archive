import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";

export default function LoginPage() {
  const {
    isLoading,
    isAuthenticated,
    loginWithRedirect,
    logout,
    user,
    getAccessTokenSilently,
  } = useAuth0();

  const [tokenStatus, setTokenStatus] = useState<string>("Not checked");

  async function testToken() {
    try {
      const token = await getAccessTokenSilently({
        authorizationParams: {
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        },
      });

      console.log("MANUAL AUTH0 ACCESS TOKEN:", token);

      setTokenStatus(
        `Token received (${token.substring(0, 30)}...)`
      );
    } catch (error) {
      console.error("AUTH0 TOKEN ERROR:", error);

      setTokenStatus(
        `Token error: ${String(error)}`
      );
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    testToken();
  }, [isAuthenticated]);

  if (isLoading) {
    return <div>Loading authentication...</div>;
  }

  if (isAuthenticated) {
    return (
      <div>
        <h1>Authenticated ✅</h1>

        <p>
          Signed in as: {user?.email ?? "No email returned"}
        </p>

        <p>
          Auth0 ID: {user?.sub ?? "No sub returned"}
        </p>

        <p>
          Token status: {tokenStatus}
        </p>

        <button
          type="button"
          onClick={testToken}
        >
          Test Get Access Token
        </button>

        <button
          type="button"
          onClick={() =>
            logout({
              logoutParams: {
                returnTo: window.location.origin,
              },
            })
          }
        >
          Log out
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1>Login</h1>

      <p>
        Sign in to continue to the credit risk platform.
      </p>

      <button
        type="button"
        onClick={() => loginWithRedirect()}
      >
        Login
      </button>
    </div>
  );
}