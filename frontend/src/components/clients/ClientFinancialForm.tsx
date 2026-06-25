import type { FormEvent } from "react";
import type { Client, ClientFinancialCreate } from "../../types";

type ClientFinancialFormProps = {
  clients: Client[];
  clientId: string;
  month: string;
  revenue: string;
  cogs: string;
  opex: string;
  cashBalance: string;
  isLoadingClients: boolean;
  isSubmitting: boolean;
  onClientIdChange: (value: string) => void;
  onMonthChange: (value: string) => void;
  onRevenueChange: (value: string) => void;
  onCogsChange: (value: string) => void;
  onOpexChange: (value: string) => void;
  onCashBalanceChange: (value: string) => void;
  onSubmit: (payload: ClientFinancialCreate) => void;
};

export function currentMonthValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function monthToApiDate(monthValue: string): string {
  return `${monthValue}-01`;
}

export default function ClientFinancialForm({
  clients,
  clientId,
  month,
  revenue,
  cogs,
  opex,
  cashBalance,
  isLoadingClients,
  isSubmitting,
  onClientIdChange,
  onMonthChange,
  onRevenueChange,
  onCogsChange,
  onOpexChange,
  onCashBalanceChange,
  onSubmit,
}: ClientFinancialFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit({
      client_id: Number(clientId),
      month: monthToApiDate(month),
      revenue: Number(revenue),
      cogs: Number(cogs),
      opex: Number(opex),
      cash_balance: Number(cashBalance),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">Client Financials</h2>
      <p className="deal-form__subtitle">Submit monthly financial data for a client</p>

      <label className="deal-form__field">
        <span className="deal-form__label">Client</span>
        <select
          className="deal-form__input"
          value={clientId}
          onChange={(e) => onClientIdChange(e.target.value)}
          required
          disabled={isLoadingClients || isSubmitting}
        >
          <option value="">Select a client</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.name}
            </option>
          ))}
        </select>
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">Month</span>
        <input
          className="deal-form__input"
          type="month"
          value={month}
          onChange={(e) => onMonthChange(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">Revenue</span>
        <input
          className="deal-form__input"
          type="number"
          min="0"
          step="any"
          value={revenue}
          onChange={(e) => onRevenueChange(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">COGS</span>
        <input
          className="deal-form__input"
          type="number"
          min="0"
          step="any"
          value={cogs}
          onChange={(e) => onCogsChange(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">OPEX</span>
        <input
          className="deal-form__input"
          type="number"
          min="0"
          step="any"
          value={opex}
          onChange={(e) => onOpexChange(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">Cash Balance</span>
        <input
          className="deal-form__input"
          type="number"
          min="0"
          step="any"
          value={cashBalance}
          onChange={(e) => onCashBalanceChange(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </label>

      <button className="deal-form__submit" type="submit" disabled={isSubmitting || isLoadingClients}>
        {isSubmitting ? "Submitting…" : "Submit"}
      </button>
    </form>
  );
}
