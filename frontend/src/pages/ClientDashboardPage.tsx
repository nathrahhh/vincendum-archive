import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import {
  getMyClient,
  getMyClientDeals,
  getMyClientFinancials,
  getMyClientForecastScenarios,
} from "../services/clientService";
import type {
  Client,
  ClientDeal,
  ClientFinancials,
  ClientForecast,
} from "../types";

export default function ClientDashboardPage() {
  const [client, setClient] = useState<Client | null>(null);
  const [deals, setDeals] = useState<ClientDeal[]>([]);
  const [financials, setFinancials] = useState<ClientFinancials | null>(null);
  const [baseForecast, setBaseForecast] = useState<ClientForecast | null>(null);
  const [bestForecast, setBestForecast] = useState<ClientForecast | null>(null);
  const [worstForecast, setWorstForecast] = useState<ClientForecast | null>(null);

  const [baseGrowthRate, setBaseGrowthRate] = useState(0.05);
  const [bestGrowthRate, setBestGrowthRate] = useState(0.08);
  const [worstGrowthRate, setWorstGrowthRate] = useState(0.02);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setIsLoading(true);
      setError(null);
      try {
        const [clientData, financialData, dealData] = await Promise.all([
          getMyClient(),
          getMyClientFinancials(),
          getMyClientDeals(),
        ]);
        if (!cancelled) {
          setClient(clientData);
          setFinancials(financialData);
          setDeals(dealData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load your client dashboard",
          );
          setClient(null);
          setFinancials(null);
          setDeals([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadProfile();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!client) {
      return;
    }

    let cancelled = false;

    async function loadScenarios() {
      setIsLoading(true);
      setError(null);
      try {
        const scenarios = await getMyClientForecastScenarios(
          baseGrowthRate,
          bestGrowthRate,
          worstGrowthRate,
        );
        if (!cancelled) {
          setBaseForecast(scenarios.base);
          setBestForecast(scenarios.best);
          setWorstForecast(scenarios.worst);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load forecast scenarios",
          );
          setBaseForecast(null);
          setBestForecast(null);
          setWorstForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadScenarios();
    return () => {
      cancelled = true;
    };
  }, [client?.id, baseGrowthRate, bestGrowthRate, worstGrowthRate]);

  async function handleClientUpdated() {
    setError(null);
    try {
      const [clientData, financialData, dealData] = await Promise.all([
        getMyClient(),
        getMyClientFinancials(),
        getMyClientDeals(),
      ]);
      setClient(clientData);
      setFinancials(financialData);
      setDeals(dealData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to refresh your client data",
      );
      throw err;
    }
  }

  return (
    <div className="clients-page">
      <ClientDetailPanel
        client={client}
        financials={financials}
        deals={deals}
        baseForecast={baseForecast}
        bestForecast={bestForecast}
        worstForecast={worstForecast}
        baseGrowthRate={baseGrowthRate}
        bestGrowthRate={bestGrowthRate}
        worstGrowthRate={worstGrowthRate}
        onBaseGrowthRateChange={setBaseGrowthRate}
        onBestGrowthRateChange={setBestGrowthRate}
        onWorstGrowthRateChange={setWorstGrowthRate}
        onClientUpdated={handleClientUpdated}
        isLoading={isLoading}
        error={error}
        mode="client"
      />
    </div>
  );
}
