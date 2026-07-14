import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import {
  getClient,
  getClientFinancials,
  getClientForecastScenarios,
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
  const [baseForecast, setBaseForecast] = useState<ClientForecast | null>(null);
  const [bestForecast, setBestForecast] = useState<ClientForecast | null>(null);
  const [worstForecast, setWorstForecast] = useState<ClientForecast | null>(null);

  const [baseGrowthRate, setBaseGrowthRate] = useState(0.05);
  const [bestGrowthRate, setBestGrowthRate] = useState(0.08);
  const [worstGrowthRate, setWorstGrowthRate] = useState(0.02);

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
    setBaseForecast(null);
    setBestForecast(null);
    setWorstForecast(null);
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
      setIsLoadingDetail(false);
    }
  }

  useEffect(() => {
    if (!selectedClient) {
      return;
    }

    const clientId = selectedClient.id;
    let cancelled = false;

    async function loadScenarios() {
      setIsLoadingDetail(true);
      setError(null);
      try {
        const scenarios = await getClientForecastScenarios(
          clientId,
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
              : "Failed to load forecast scenarios"
          );
          setBaseForecast(null);
          setBestForecast(null);
          setWorstForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingDetail(false);
        }
      }
    }

    loadScenarios();
    return () => {
      cancelled = true;
    };
  }, [selectedClient?.id, baseGrowthRate, bestGrowthRate, worstGrowthRate]);

  async function handleClientUpdated() {
    if (!selectedClient) {
      return;
    }

    const clientId = selectedClient.id;
    setError(null);
    try {
      const [clientData, clientsData] = await Promise.all([
        getClient(clientId),
        getClients(),
      ]);
      setSelectedClient(clientData);
      setClients(clientsData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to refresh client data"
      );
      throw err;
    }
  }

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


      <ClientDetailPanel
        client={selectedClient}
        financials={financials}
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
        isLoading={isLoadingDetail}
        error={error}
      />


    </div>
  );
}
