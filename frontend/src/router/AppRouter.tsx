import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout";
import {
  defaultPathForRole,
  useCurrentUser,
} from "../auth/CurrentUserProvider";
import AuditLogsPage from "../pages/AuditLogsPage";
import ApplyPage from "../pages/ApplyPage";
import ClientApplicationsPage from "../pages/ClientApplicationsPage";
import ClientDashboardPage from "../pages/ClientDashboardPage";
import ClientsPage from "../pages/ClientsPage";
import BreachesPage from "../pages/BreachesPage";
import DashboardPage from "../pages/DashboardPage";
import ClientFinancialsPage from "../pages/ClientFinancialsPage";
import DealPage from "../pages/DealPage";
import EvaluationsPage from "../pages/EvaluationsPage";
import FinancialEvaluationsPage from "../pages/FinancialEvaluationsPage";
import ProfilePage from "../pages/ProfilePage";

export default function AppRouter() {
  const { role, isLoading } = useCurrentUser();
  const defaultPath = defaultPathForRole(role);

  if (isLoading) {
    return <div>Loading account...</div>;
  }

  return (
    <Routes>
      <Route path="/apply/:lenderSlug" element={<ApplyPage />} />

      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to={defaultPath} replace />} />

        {role === "client" ? (
          <>
            <Route path="/client" element={<ClientDashboardPage />} />
            <Route
              path="/client-dashboard"
              element={<Navigate to="/client" replace />}
            />
            <Route path="/deal" element={<DealPage />} />
            <Route path="/client-financials" element={<ClientFinancialsPage />} />
            <Route path="*" element={<Navigate to="/client" replace />} />
          </>
        ) : (
          <>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/evaluations" element={<EvaluationsPage />} />
            <Route
              path="/financial-evaluations"
              element={<FinancialEvaluationsPage />}
            />
            <Route path="/breaches" element={<BreachesPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/client-applications" element={<ClientApplicationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/deal" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Route>
    </Routes>
  );
}
