import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import {
  getMyClient,
  getMyClientDeals,
  getMyClientFinancials,
} from "../services/clientService";
import type {
  Client,
  ClientDeal,
  ClientFinancials,
} from "../types";

export default function ClientDashboardPage() {
  const [client, setClient] = useState<Client | null>(null);
  const [deals, setDeals] = useState<ClientDeal[]>([]);
  const [financials, setFinancials] = useState<ClientFinancials | null>(null);

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
        onClientUpdated={handleClientUpdated}
        isLoading={isLoading}
        error={error}
        mode="client"
      />
    </div>
  );
}
