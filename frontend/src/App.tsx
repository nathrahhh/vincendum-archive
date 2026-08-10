import { Route, Routes } from "react-router-dom";
import AuthAccessTokenBridge from "./auth/AuthAccessTokenBridge";
import ProtectedRoute from "./auth/ProtectedRoute";
import RequireLenderOnboarded from "./auth/RequireLenderOnboarded";
import { DevRoleProvider } from "./devRole";
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
              <OnboardingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <RequireLenderOnboarded>
                <DevRoleProvider>
                  <AppRouter />
                </DevRoleProvider>
              </RequireLenderOnboarded>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
