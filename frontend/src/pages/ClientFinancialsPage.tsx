import { useEffect, useState } from "react";
import ClientFinancialForm, { currentMonthValue } from "../components/clients/ClientFinancialForm";
import FinancialStatementUpload from "../components/clients/FinancialStatementUpload";
import { getClients, submitClientFinancial } from "../services/clientService";
import type { Client, ClientFinancialCreate, FinancialStatementExtraction } from "../types";

export default function ClientFinancialsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState("");
  const [month, setMonth] = useState(currentMonthValue);
  const [revenue, setRevenue] = useState("");
  const [cogs, setCogs] = useState("");
  const [grossProfit, setGrossProfit] = useState("");
  const [opex, setOpex] = useState("");
  const [cashBalance, setCashBalance] = useState("");
  const [isLoadingClients, setIsLoadingClients] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadClients() {
      setIsLoadingClients(true);
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
          setIsLoadingClients(false);
        }
      }
    }

    loadClients();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleFinancialExtraction(data: FinancialStatementExtraction) {
    if (data.revenue !== null) {
      setRevenue(String(data.revenue));
    }
    if (data.cogs !== null) {
      setCogs(String(Math.abs(data.cogs)));
    }
    if (data.gross_profit !== null) {
      setGrossProfit(String(data.gross_profit));
    }
    if (data.opex !== null) {
      setOpex(String(Math.abs(data.opex)));
    }
    if (data.cash !== null) {
      setCashBalance(String(data.cash));
    }
  }

  async function handleSubmit(payload: ClientFinancialCreate) {
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await submitClientFinancial(payload);
      setSuccess(response.message);
      setRevenue("");
      setCogs("");
      setGrossProfit("");
      setOpex("");
      setCashBalance("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit client financials");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="client-financials-page">
      {error ? <p className="dashboard-error">{error}</p> : null}
      {success ? <p className="client-financials__success">{success}</p> : null}
      <FinancialStatementUpload onExtract={handleFinancialExtraction} />
      <ClientFinancialForm
        clients={clients}
        clientId={clientId}
        month={month}
        revenue={revenue}
        cogs={cogs}
        grossProfit={grossProfit}
        opex={opex}
        cashBalance={cashBalance}
        isLoadingClients={isLoadingClients}
        isSubmitting={isSubmitting}
        onClientIdChange={setClientId}
        onMonthChange={setMonth}
        onRevenueChange={setRevenue}
        onCogsChange={setCogs}
        onGrossProfitChange={setGrossProfit}
        onOpexChange={setOpex}
        onCashBalanceChange={setCashBalance}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
