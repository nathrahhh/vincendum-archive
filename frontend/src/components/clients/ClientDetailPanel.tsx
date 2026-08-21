import { useState } from "react";
import type {
  Client,
  ClientDeal,
  ClientFinancials,
  ClientForecast,
} from "../../types";
import ClientDealsTab from "./ClientDealsTab";
import ClientDocumentsTab from "./ClientDocumentsTab";
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
  /** Admin keeps edit/invite controls. Client is read-only overview. */
  mode?: "admin" | "client";
  /** Optional deals override (used by client POV from GET /client/me/deals). */
  deals?: ClientDeal[];
};

type ClientDetailTab =
  | "Overview"
  | "Deals"
  | "Financials"
  | "Forecast"
  | "Documents";

const ADMIN_TABS: ClientDetailTab[] = [
  "Overview",
  "Deals",
  "Financials",
  "Forecast",
  "Documents",
];

const CLIENT_TABS: ClientDetailTab[] = [
  "Overview",
  "Deals",
  "Financials",
  "Documents",
];

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
  mode = "admin",
  deals,
}: ClientDetailPanelProps) {
  const [activeTab, setActiveTab] =
    useState<ClientDetailTab>("Overview");

  if (!client) {
    return (
      <aside className="clients-panel">
        <p className="clients-panel__hint">
          {mode === "client"
            ? "Loading your client details…"
            : "Select a client to view details."}
        </p>
      </aside>
    );
  }

  const resolvedDeals = deals ?? client.deals ?? [];
  const tabs = mode === "client" ? CLIENT_TABS : ADMIN_TABS;

  return (
    <aside className="clients-panel">
      <h2 className="clients-panel__title">{client.name}</h2>

      <p className="clients-panel__meta">
        Industry: {client.industry}
      </p>

      <nav className="clients-panel__tabs">
        {tabs.map((tab) => (
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
        <p className="clients-panel__hint">
          Loading client data…
        </p>
      )}

      {activeTab === "Overview" ? (
        <ClientOverviewTab
          client={client}
          onClientUpdated={onClientUpdated}
          mode={mode}
        />
      ) : null}

      {activeTab === "Deals" ? (
        <ClientDealsTab deals={resolvedDeals} />
      ) : null}

      {activeTab === "Financials" ? (
        <ClientFinancialsTab financials={financials} />
      ) : null}

      {activeTab === "Forecast" && mode === "admin" ? (
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
          forecastApi="admin"
        />
      ) : null}

      {activeTab === "Documents" ? (
        mode === "admin" ? (
          <ClientDocumentsTab clientId={client.id} />
        ) : (
          <ClientDocumentsTab />
        )
      ) : null}
    </aside>
  );
}