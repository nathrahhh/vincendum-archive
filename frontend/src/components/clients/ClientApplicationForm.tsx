import type { FormEvent } from "react";
import type { ClientApplicationCreate } from "../../types";

const INDUSTRIES = [
  "Manufacturing",
  "Retail",
  "Technology",
  "Healthcare",
  "Energy",
] as const;

type ClientApplicationFormProps = {
  businessName: string;
  industry: string;
  creditLimit: string;
  isSubmitting: boolean;
  onBusinessNameChange: (value: string) => void;
  onIndustryChange: (value: string) => void;
  onCreditLimitChange: (value: string) => void;
  onSubmit: (payload: ClientApplicationCreate) => void;
};

export default function ClientApplicationForm({
  businessName,
  industry,
  creditLimit,
  isSubmitting,
  onBusinessNameChange,
  onIndustryChange,
  onCreditLimitChange,
  onSubmit,
}: ClientApplicationFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit({
      name: businessName.trim(),
      industry: industry.trim(),
      credit_limit: Number(creditLimit),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">Client Application</h2>
      <p className="deal-form__subtitle">Apply for a credit facility</p>

      <fieldset className="deal-form__section" disabled={isSubmitting}>
        <legend className="deal-form__section-title">Application Details</legend>

        <label className="deal-form__field">
          <span className="deal-form__label">Business Name</span>
          <input
            className="deal-form__input"
            type="text"
            value={businessName}
            onChange={(e) => onBusinessNameChange(e.target.value)}
            placeholder="e.g. Acme Healthcare Ltd"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Industry</span>
          <select
            className="deal-form__input"
            value={industry}
            onChange={(e) => onIndustryChange(e.target.value)}
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

        <label className="deal-form__field">
          <span className="deal-form__label">Requested Credit Limit (USD)</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={creditLimit}
            onChange={(e) => onCreditLimitChange(e.target.value)}
            placeholder="e.g. 1500000"
            required
          />
        </label>
      </fieldset>

      <button className="deal-form__submit" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Submitting…" : "Submit Application"}
      </button>
    </form>
  );
}
