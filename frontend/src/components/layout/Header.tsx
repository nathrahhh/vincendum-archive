import { useLocation } from "react-router-dom";

const titles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/client": "My Client",
  "/client-dashboard": "My Client",
  "/deal": "Deal",
  "/apply": "Apply",
  "/client-financials": "Client Financials",
  "/client/bank-transactions": "Bank Transactions",
  "/evaluations": "Evaluations",
  "/financial-evaluations": "Financial Evaluations",
  "/breaches": "Breaches",
  "/clients": "Clients",
  "/client-applications": "Client Applications",
};

export default function Header() {
  const { pathname } = useLocation();
  const title = titles[pathname] ?? "Credit Risk Engine";

  return (
    <header className="app-header">
      <h1 className="app-header__title">{title}</h1>
      <p className="app-header__subtitle">Private credit pre-trade risk</p>
    </header>
  );
}
