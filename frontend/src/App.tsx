import { Route, Routes } from "react-router-dom";
import AuthAccessTokenBridge from "./auth/AuthAccessTokenBridge";
import { CurrentUserProvider } from "./auth/CurrentUserProvider";
import ProtectedRoute from "./auth/ProtectedRoute";
import RequireLenderOnboarded from "./auth/RequireLenderOnboarded";
import ClientInvitationPage from "./pages/ClientInvitationPage";
import LoginPage from "./pages/LoginPage";
import OnboardingPage from "./pages/OnboardingPage";
import { AppRouter } from "./router";

export default function App() {
  return (
    <>
      <AuthAccessTokenBridge />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/invite/:token" element={<ClientInvitationPage />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <CurrentUserProvider>
                <OnboardingPage />
              </CurrentUserProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <CurrentUserProvider>
                <RequireLenderOnboarded>
                  <AppRouter />
                </RequireLenderOnboarded>
              </CurrentUserProvider>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
