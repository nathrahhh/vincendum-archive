import { StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, useNavigate } from "react-router-dom";
import { Auth0Provider, type AppState } from "@auth0/auth0-react";
import App from "./App";
import "./index.css";
import AuthAccessTokenBridge from "./auth/AuthAccessTokenBridge";

function Auth0ProviderWithRedirect({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  return (
    <Auth0Provider
      domain={import.meta.env.VITE_AUTH0_DOMAIN}
      clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        scope: "openid profile email",
        ...(import.meta.env.VITE_AUTH0_AUDIENCE
          ? { audience: import.meta.env.VITE_AUTH0_AUDIENCE }
          : {}),
      }}
      onRedirectCallback={(appState?: AppState) => {
        navigate(appState?.returnTo ?? window.location.pathname, {
          replace: true,
        });
      }}
    >
      {children}
    </Auth0Provider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Auth0ProviderWithRedirect>
        <AuthAccessTokenBridge />
        <App />
      </Auth0ProviderWithRedirect>
    </BrowserRouter>
  </StrictMode>,
);
