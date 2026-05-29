import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout";
import BreachesPage from "../pages/BreachesPage";
import DashboardPage from "../pages/DashboardPage";
import DealPage from "../pages/DealPage";
import EvaluationsPage from "../pages/EvaluationsPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/deal" element={<DealPage />} />
        <Route path="/evaluations" element={<EvaluationsPage />} />
        <Route path="/breaches" element={<BreachesPage />} />
      </Route>
    </Routes>
  );
}
