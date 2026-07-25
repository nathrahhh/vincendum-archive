import { useState } from "react";
import type { Client, ClientFinancials, ClientForecast } from "../../types";
import ClientDealsTab from "./ClientDealsTab";
import ClientFinancialsTab from "./ClientFinancialsTab";
import ClientForecastTab from "./ClientForecastTab";
import ClientOverviewTab from "./ClientOverviewTab";

type ClientDetailPanelProps = {
  client: Client | null;
  financials: ClientFinancials | null;
  baseForecast: ClientForecast | null;
  bestForecast: ClientForecast | null;
  worstForecast: ClientForecast | null;
  baseGrowthRate: number;
  bestGrowthRate: number;
  worstGrowthRate: number;
  onBaseGrowthRateChange: (value: number) => void;
  onBestGrowthRateChange: (value: number) => void;
  onWorstGrowthRateChange: (value: number) => void;
  onClientUpdated: () => Promise<void> | void;
  isLoading: boolean;
  error: string | null;
};

type ClientDetailTab = "Overview" | "Deals" | "Financials" | "Forecast";

const TABS: ClientDetailTab[] = ["Overview", "Deals", "Financials", "Forecast"];

export default function ClientDetailPanel({
  client,
  financials,
  baseForecast,
  bestForecast,
  worstForecast,
  baseGrowthRate,
  bestGrowthRate,
  worstGrowthRate,
  onBaseGrowthRateChange,
  onBestGrowthRateChange,
  onWorstGrowthRateChange,
  onClientUpdated,
  isLoading,
  error,
}: ClientDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<ClientDetailTab>("Overview");

  if (!client) {
    return (
      <aside className="clients-panel">
        <p className="clients-panel__hint">Select a client to view details.</p>
      </aside>
    );
  }

  const deals = client.deals ?? [];

  return (
    <aside className="clients-panel">
      <h2 className="clients-panel__title">{client.name}</h2>

      <p className="clients-panel__meta">Industry: {client.industry}</p>

      <nav className="clients-panel__tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            className={
              activeTab === tab
                ? "clients-panel__tab clients-panel__tab--active"
                : "clients-panel__tab"
            }
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      {error && <p className="dashboard-error">{error}</p>}

      {isLoading && (
        <p className="clients-panel__hint">Loading client data…</p>
      )}

      {activeTab === "Overview" ? (
        <ClientOverviewTab client={client} onClientUpdated={onClientUpdated} />
      ) : null}

      {activeTab === "Deals" ? <ClientDealsTab deals={deals} /> : null}

      {activeTab === "Financials" ? (
        <ClientFinancialsTab financials={financials} />
      ) : null}

      {activeTab === "Forecast" ? (
        <ClientForecastTab
          clientId={client.id}
          financials={financials}
          baseForecast={baseForecast}
          bestForecast={bestForecast}
          worstForecast={worstForecast}
          baseGrowthRate={baseGrowthRate}
          bestGrowthRate={bestGrowthRate}
          worstGrowthRate={worstGrowthRate}
          onBaseGrowthRateChange={onBaseGrowthRateChange}
          onBestGrowthRateChange={onBestGrowthRateChange}
          onWorstGrowthRateChange={onWorstGrowthRateChange}
          isLoading={isLoading}
        />
      ) : null}
    </aside>
  );
}
