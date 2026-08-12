import { useState } from "react";
import ClientFinancialForm, { currentMonthValue } from "../components/clients/ClientFinancialForm";
import FinancialStatementUpload from "../components/clients/FinancialStatementUpload";
import { submitClientFinancial } from "../services/clientService";
import type { ClientFinancialCreate, FinancialStatementExtraction } from "../types";

export default function ClientFinancialsPage() {
  const [month, setMonth] = useState(currentMonthValue);
  const [revenue, setRevenue] = useState("");
  const [cogs, setCogs] = useState("");
  const [grossProfit, setGrossProfit] = useState("");
  const [opex, setOpex] = useState("");
  const [cashBalance, setCashBalance] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
        month={month}
        revenue={revenue}
        cogs={cogs}
        grossProfit={grossProfit}
        opex={opex}
        cashBalance={cashBalance}
        isSubmitting={isSubmitting}
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
