import { useState } from "react";
import type { FormEvent } from "react";
import type { DealPayload } from "../../types";

type DealFormProps = {
  onSubmit: (deal: DealPayload) => void;
  isLoading?: boolean;
};

const INDUSTRIES = [
  "Manufacturing",
  "Retail",
  "Technology",
  "Healthcare",
  "Energy",
] as const;

export default function DealForm({ onSubmit, isLoading = false }: DealFormProps) {
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [annualTurnover, setAnnualTurnover] = useState("");
  const [existingDebt, setExistingDebt] = useState("");
  const [requestedLoanAmount, setRequestedLoanAmount] = useState("");
  const [loanTermMonths, setLoanTermMonths] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit({
      name: businessName.trim(),
      value: Number(requestedLoanAmount),
      industry: industry.trim(),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">Loan Application</h2>
      <p className="deal-form__subtitle">Submit your business loan request for evaluation</p>

      <fieldset className="deal-form__section" disabled={isLoading}>
        <legend className="deal-form__section-title">Business Information</legend>

        <label className="deal-form__field">
          <span className="deal-form__label">Business Name</span>
          <input
            className="deal-form__input"
            type="text"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            placeholder="e.g. Acme Healthcare Ltd"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Industry</span>
          <select
            className="deal-form__input"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
          >
            <option value="">Select an industry</option>
            {INDUSTRIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </fieldset>

      <fieldset className="deal-form__section" disabled={isLoading}>
        <legend className="deal-form__section-title">Contact</legend>

        <label className="deal-form__field">
          <span className="deal-form__label">Contact Email</span>
          <input
            className="deal-form__input"
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            placeholder="contact@business.com"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Contact Phone (optional)</span>
          <input
            className="deal-form__input"
            type="tel"
            value={contactPhone}
            onChange={(e) => setContactPhone(e.target.value)}
            placeholder="+1 555 000 0000"
          />
        </label>
      </fieldset>

      <fieldset className="deal-form__section" disabled={isLoading}>
        <legend className="deal-form__section-title">Financial Details</legend>

        <label className="deal-form__field">
          <span className="deal-form__label">Annual Turnover (USD)</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={annualTurnover}
            onChange={(e) => setAnnualTurnover(e.target.value)}
            placeholder="e.g. 5000000"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Existing Debt (USD)</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={existingDebt}
            onChange={(e) => setExistingDebt(e.target.value)}
            placeholder="e.g. 1200000"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Requested Loan Amount (USD)</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={requestedLoanAmount}
            onChange={(e) => setRequestedLoanAmount(e.target.value)}
            placeholder="e.g. 1500000"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Loan Term (Months)</span>
          <input
            className="deal-form__input"
            type="number"
            min="1"
            step="1"
            value={loanTermMonths}
            onChange={(e) => setLoanTermMonths(e.target.value)}
            placeholder="e.g. 36"
            required
          />
        </label>
      </fieldset>

      <button className="deal-form__submit" type="submit" disabled={isLoading}>
        {isLoading ? "Submitting…" : "Submit Application"}
      </button>
    </form>
  );
}
