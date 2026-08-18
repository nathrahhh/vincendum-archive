import type { FormEvent } from "react";

const INDUSTRIES = [
  "Manufacturing",
  "Retail",
  "Technology",
  "Healthcare",
  "Energy",
] as const;

type ClientApplicationFormProps = {
  businessName: string;
  registeredBusinessName: string;
  industry: string;
  companiesHouseNumber: string;
  incorporationYear: string;
  headcount: string;
  revenueLastFy: string;
  creditLimit: string;
  isSubmitting: boolean;
  onBusinessNameChange: (value: string) => void;
  onRegisteredBusinessNameChange: (value: string) => void;
  onIndustryChange: (value: string) => void;
  onCompaniesHouseNumberChange: (value: string) => void;
  onIncorporationYearChange: (value: string) => void;
  onHeadcountChange: (value: string) => void;
  onRevenueLastFyChange: (value: string) => void;
  onCreditLimitChange: (value: string) => void;
  onSubmit: () => void;
};

export default function ClientApplicationForm({
  businessName,
  registeredBusinessName,
  industry,
  companiesHouseNumber,
  incorporationYear,
  headcount,
  revenueLastFy,
  creditLimit,
  isSubmitting,
  onBusinessNameChange,
  onRegisteredBusinessNameChange,
  onIndustryChange,
  onCompaniesHouseNumberChange,
  onIncorporationYearChange,
  onHeadcountChange,
  onRevenueLastFyChange,
  onCreditLimitChange,
  onSubmit,
}: ClientApplicationFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
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
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Registered Business Name</span>
          <input
            className="deal-form__input"
            type="text"
            value={registeredBusinessName}
            onChange={(e) => onRegisteredBusinessNameChange(e.target.value)}
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
          <span className="deal-form__label">Companies House Number</span>
          <input
            className="deal-form__input"
            type="text"
            value={companiesHouseNumber}
            onChange={(e) => onCompaniesHouseNumberChange(e.target.value)}
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Incorporation Year</span>
          <input
            className="deal-form__input"
            type="number"
            min="1800"
            step="1"
            value={incorporationYear}
            onChange={(e) => onIncorporationYearChange(e.target.value)}
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Headcount</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="1"
            value={headcount}
            onChange={(e) => onHeadcountChange(e.target.value)}
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Revenue Last FY</span>
          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={revenueLastFy}
            onChange={(e) => onRevenueLastFyChange(e.target.value)}
          />
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
