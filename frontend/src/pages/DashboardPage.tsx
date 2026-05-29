import { useEffect, useState } from "react";
import {
  ExposureChartPlaceholder,
  KpiCard,
  PortfolioTable,
  RecentDeals,
} from "../components/dashboard";
import { getPortfolio } from "../services/portfolioService";
import type { Position } from "../types";

const MAX_PORTFOLIO_CAPITAL = 100_000_000;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export default function DashboardPage() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPortfolio() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPortfolio();
        if (!cancelled) {
          setPositions(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load portfolio");
          setPositions([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadPortfolio();
    return () => {
      cancelled = true;
    };
  }, []);

  const portfolioValue = positions.reduce((sum, p) => sum + p.value, 0);
  const utilisationPct = (portfolioValue / MAX_PORTFOLIO_CAPITAL) * 100;

  return (
    <div className="dashboard">
      <div className="dashboard-kpis">
        <KpiCard
          label="Portfolio Value"
          value={isLoading ? "—" : formatCurrency(portfolioValue)}
          hint="Total deployed capital"
        />
        <KpiCard
          label="Utilisation %"
          value={isLoading ? "—" : formatPercent(utilisationPct)}
          hint="Of $100M capital base"
        />
        <KpiCard label="Risk Status" value="—" hint="Connect breaches API on Evaluations" />
      </div>

      <div className="dashboard-grid">
        <PortfolioTable positions={positions} isLoading={isLoading} error={error} />
        <ExposureChartPlaceholder />
      </div>

      <RecentDeals />
    </div>
  );
}
