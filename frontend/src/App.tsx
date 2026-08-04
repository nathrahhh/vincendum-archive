import { Route, Routes } from "react-router-dom";
import AuthAccessTokenBridge from "./auth/AuthAccessTokenBridge";
import ProtectedRoute from "./auth/ProtectedRoute";
import { DevRoleProvider } from "./devRole";
import LoginPage from "./pages/LoginPage";
import { AppRouter } from "./router";

export default function App() {
  return (
    <>
      <AuthAccessTokenBridge />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <DevRoleProvider>
                <AppRouter />
              </DevRoleProvider>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
