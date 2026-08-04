import { useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { setAccessTokenGetter } from "./accessToken";

/**
 * Bridges Auth0's `getAccessTokenSilently` into the non-React API client.
 * Renders nothing.
 */
export default function AuthAccessTokenBridge() {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    if (!isAuthenticated) {
      setAccessTokenGetter(null);
      return;
    }

    const audience = import.meta.env.VITE_AUTH0_AUDIENCE as string | undefined;

    setAccessTokenGetter(() =>
      getAccessTokenSilently(
        audience
          ? { authorizationParams: { audience } }
          : undefined,
      ),
    );

    return () => {
      setAccessTokenGetter(null);
    };
  }, [isAuthenticated, getAccessTokenSilently]);

  return null;
}
