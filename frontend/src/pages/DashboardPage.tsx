import { useEffect, useState } from "react";
import { ExposureChart, KpiCard, PortfolioTable, RecentDeals } from "../components/dashboard";
import { fetchIndustryExposure } from "../services/lenderService";
import { getPortfolio } from "../services/portfolioService";
import type { IndustryExposure, Position } from "../types";

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
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [utilisationPct, setUtilisationPct] = useState(0);
  const [industryExposure, setIndustryExposure] = useState<IndustryExposure[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [industryExposureLoading, setIndustryExposureLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPortfolio() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPortfolio();
        if (!cancelled) {
          setPositions(data.positions);
          setPortfolioValue(data.total_portfolio_value);
          setUtilisationPct(data.capital_utilization_pct);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load portfolio");
          setPositions([]);
          setPortfolioValue(0);
          setUtilisationPct(0);
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

  useEffect(() => {
    let cancelled = false;

    async function loadIndustryExposure() {
      setIndustryExposureLoading(true);
      try {
        const data = await fetchIndustryExposure();
        if (!cancelled) {
          setIndustryExposure(data);
        }
      } catch (err) {
        console.error("Failed to load industry exposure", err);
        if (!cancelled) {
          setIndustryExposure([]);
        }
      } finally {
        if (!cancelled) {
          setIndustryExposureLoading(false);
        }
      }
    }

    loadIndustryExposure();
    return () => {
      cancelled = true;
    };
  }, []);

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
          hint="Of $10M capital base"
        />
        <KpiCard label="Risk Status" value="—" hint="Connect breaches API on Evaluations" />
      </div>

      <div className="dashboard-grid">
        <PortfolioTable positions={positions} isLoading={isLoading} error={error} />
        <ExposureChart
          exposure={industryExposure}
          isLoading={industryExposureLoading}
        />
      </div>

      <RecentDeals />
    </div>
  );
}
