import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import {
  getClient,
  getClientFinancials,
  getClientForecast,
  getClients,
} from "../services/clientService";
import type { Client, ClientFinancials, ClientForecast } from "../types";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [financials, setFinancials] = useState<ClientFinancials | null>(null);
  const [forecast, setForecast] = useState<ClientForecast | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadClients() {
      setIsLoadingList(true);
      setError(null);
      try {
        const data = await getClients();
        if (!cancelled) {
          setClients(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load clients");
          setClients([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingList(false);
        }
      }
    }

    loadClients();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleClientSelect(client: Client) {
    setSelectedClient(client);
  }

  useEffect(() => {
    if (!selectedClient) {
      setFinancials(null);
      setForecast(null);
      return;
    }

    const clientId = selectedClient.id;
    let cancelled = false;

    async function loadClientData() {
      setIsLoadingDetail(true);
      setError(null);
      try {
        const [clientData, financialsData, forecastData] = await Promise.all([
          getClient(clientId),
          getClientFinancials(clientId),
          getClientForecast(clientId),
        ]);
        if (!cancelled) {
          setSelectedClient(clientData);
          setFinancials(financialsData);
          setForecast(forecastData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load client data");
          setFinancials(null);
          setForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingDetail(false);
        }
      }
    }

    loadClientData();
    return () => {
      cancelled = true;
    };
  }, [selectedClient?.id]);

  return (
    <div className="clients-page">
      <section className="dashboard-panel clients-page__list">
        <h2 className="dashboard-panel__title">Clients</h2>
        {isLoadingList ? <p className="dashboard-panel__subtitle">Loading clients…</p> : null}
        {error && !selectedClient ? <p className="dashboard-error">{error}</p> : null}
        {!isLoadingList && clients.length === 0 ? (
          <p className="dashboard-panel__subtitle">No clients found.</p>
        ) : null}
        {!isLoadingList && clients.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table clients-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Industry</th>
                  <th>Credit Limit</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr
                    key={client.id}
                    className={
                      selectedClient?.id === client.id
                        ? "clients-table__row clients-table__row--active"
                        : "clients-table__row"
                    }
                    onClick={() => handleClientSelect(client)}
                  >
                    <td>{client.name}</td>
                    <td>{client.industry}</td>
                    <td className="dashboard-table__num">{formatCurrency(client.credit_limit)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <ClientDetailPanel
        client={selectedClient}
        financials={financials}
        forecast={forecast}
        isLoading={isLoadingDetail}
        error={selectedClient ? error : null}
      />
    </div>
  );
}
