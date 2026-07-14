import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import {
  getClient,
  getClientFinancials,
  getClientForecast,
  getClients,
} from "../services/clientService";
import type {
  Client,
  ClientFinancials,
  ClientForecast,
} from "../types";

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
  const [revenueGrowthRate, setRevenueGrowthRate] = useState(5);

  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadClients() {
      try {
        setIsLoadingList(true);
        const data = await getClients();
        setClients(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load clients"
        );
      } finally {
        setIsLoadingList(false);
      }
    }

    loadClients();
  }, []);

  async function handleClientSelect(client: Client) {
    setSelectedClient(client);
    setFinancials(null);
    setForecast(null);
    setError(null);
    setIsLoadingDetail(true);

    try {
      const clientData = await getClient(client.id);
      setSelectedClient(clientData);

      const financialData = await getClientFinancials(client.id);
      setFinancials(financialData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load client data"
      );
    } finally {
      setIsLoadingDetail(false);
    }
  }

  useEffect(() => {
    if (!selectedClient) {
      setForecast(null);
      return;
    }

    const clientId = selectedClient.id;
    let cancelled = false;

    async function loadForecast() {
      setIsLoadingDetail(true);
      setError(null);
      try {
        const forecastData = await getClientForecast(
          clientId,
          revenueGrowthRate / 100,
        );
        if (!cancelled) {
          setForecast(forecastData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load client forecast"
          );
          setForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingDetail(false);
        }
      }
    }

    loadForecast();
    return () => {
      cancelled = true;
    };
  }, [selectedClient?.id, revenueGrowthRate]);

  return (
    <div className="clients-page">

      <section className="dashboard-panel clients-page__list">

        <h2 className="dashboard-panel__title">
          Clients
        </h2>


        {isLoadingList && (
          <p className="dashboard-panel__subtitle">
            Loading clients...
          </p>
        )}


        {clients.length > 0 && (
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

                {clients.map((client)=>(
                  <tr
                    key={client.id}
                    onClick={() => handleClientSelect(client)}
                    className={
                      selectedClient?.id === client.id
                      ? "clients-table__row clients-table__row--active"
                      : "clients-table__row"
                    }
                  >

                    <td>{client.name}</td>

                    <td>{client.industry}</td>

                    <td className="dashboard-table__num">
                      {formatCurrency(client.credit_limit)}
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        )}

      </section>


      <div>
        <label className="deal-form__field">
          <span className="deal-form__label">Revenue Growth Rate (%)</span>
          <input
            className="deal-form__input"
            type="number"
            step="any"
            value={revenueGrowthRate}
            onChange={(e) => setRevenueGrowthRate(Number(e.target.value))}
          />
        </label>

        <ClientDetailPanel
          client={selectedClient}
          financials={financials}
          forecast={forecast}
          isLoading={isLoadingDetail}
          error={error}
        />
      </div>


    </div>
  );
}
