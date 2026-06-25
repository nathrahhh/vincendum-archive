import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout";
import { defaultPathForRole, useDevRole } from "../devRole";
import ClientsPage from "../pages/ClientsPage";
import BreachesPage from "../pages/BreachesPage";
import DashboardPage from "../pages/DashboardPage";
import ClientFinancialsPage from "../pages/ClientFinancialsPage";
import DealPage from "../pages/DealPage";
import EvaluationsPage from "../pages/EvaluationsPage";

export default function AppRouter() {
  const { role } = useDevRole();
  const defaultPath = defaultPathForRole(role);

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to={defaultPath} replace />} />

        {role === "client" ? (
          <>
            <Route path="/deal" element={<DealPage />} />
            <Route path="/client-financials" element={<ClientFinancialsPage />} />
            <Route path="*" element={<Navigate to="/deal" replace />} />
          </>
        ) : (
          <>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/evaluations" element={<EvaluationsPage />} />
            <Route path="/breaches" element={<BreachesPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/deal" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        )}
      </Route>
    </Routes>
  );
}
