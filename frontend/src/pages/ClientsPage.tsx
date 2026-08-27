import { useEffect, useState } from "react";
import { ClientDetailPanel } from "../components/clients";
import { fetchClientDeals } from "../api/deals";
import {
  getClient,
  getClientFinancials,
  getClients,
} from "../services/clientService";
import type {
  Client,
  ClientDeal,
  ClientFinancials,
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
  const [deals, setDeals] = useState<ClientDeal[]>([]);

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
    setDeals([]);
    setError(null);
    setIsLoadingDetail(true);

    try {
      const [clientData, financialData, dealsData] = await Promise.all([
        getClient(client.id),
        getClientFinancials(client.id),
        fetchClientDeals(client.id),
      ]);
      setSelectedClient(clientData);
      setFinancials(financialData);
      setDeals(
        dealsData.map((deal) => ({
          id: deal.id,
          name: deal.name,
          value: deal.value,
          industry: clientData.industry,
          status: deal.status ?? "",
        })),
      );
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
        deals={deals}
        onClientUpdated={handleClientUpdated}
        isLoading={isLoadingDetail}
        error={error}
      />


    </div>
  );
}
