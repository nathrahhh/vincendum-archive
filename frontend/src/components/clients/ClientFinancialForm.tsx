import type { FormEvent } from "react";
import type { ClientFinancialCreate } from "../../types";

type ClientFinancialFormProps = {
  month: string;
  revenue: string;
  cogs: string;
  grossProfit: string;
  opex: string;
  cashBalance: string;
  isSubmitting: boolean;
  onMonthChange: (value: string) => void;
  onRevenueChange: (value: string) => void;
  onCogsChange: (value: string) => void;
  onGrossProfitChange: (value: string) => void;
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
  month,
  revenue,
  cogs,
  grossProfit,
  opex,
  cashBalance,
  isSubmitting,
  onMonthChange,
  onRevenueChange,
  onCogsChange,
  onGrossProfitChange,
  onOpexChange,
  onCashBalanceChange,
  onSubmit,
}: ClientFinancialFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit({
      month: monthToApiDate(month),
      revenue: Number(revenue),
      cogs: Number(cogs),
      gross_profit: Number(grossProfit),
      opex: Number(opex),
      cash_balance: Number(cashBalance),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">Client Financials</h2>
      <p className="deal-form__subtitle">Submit monthly financial data for a client</p>

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
        <span className="deal-form__label">Gross Profit</span>
        <input
          className="deal-form__input"
          type="number"
          min="0"
          step="any"
          value={grossProfit}
          onChange={(e) => onGrossProfitChange(e.target.value)}
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

      <button className="deal-form__submit" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Submitting…" : "Submit"}
      </button>
    </form>
  );
}
