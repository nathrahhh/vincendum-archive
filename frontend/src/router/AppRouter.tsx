import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout";
import {
  defaultPathForRole,
  useCurrentUser,
} from "../auth/CurrentUserProvider";
import ApplyPage from "../pages/ApplyPage";
import ClientApplicationsPage from "../pages/ClientApplicationsPage";
import ClientDashboardPage from "../pages/ClientDashboardPage";
import ClientsPage from "../pages/ClientsPage";
import BreachesPage from "../pages/BreachesPage";
import DashboardPage from "../pages/DashboardPage";
import ClientFinancialsPage from "../pages/ClientFinancialsPage";
import DealPage from "../pages/DealPage";
import EvaluationsPage from "../pages/EvaluationsPage";

export default function AppRouter() {
  const { role, isLoading } = useCurrentUser();
  const defaultPath = defaultPathForRole(role);

  if (isLoading) {
    return <div>Loading account...</div>;
  }

  return (
    <Routes>
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
            <Route path="/apply" element={<ApplyPage />} />
            <Route path="/client-financials" element={<ClientFinancialsPage />} />
            <Route path="*" element={<Navigate to="/client" replace />} />
          </>
        ) : (
          <>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/evaluations" element={<EvaluationsPage />} />
            <Route path="/breaches" element={<BreachesPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/client-applications" element={<ClientApplicationsPage />} />
            <Route path="/deal" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Route>
    </Routes>
  );
}
