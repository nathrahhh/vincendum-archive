
import { useState } from "react";
import type { FormEvent } from "react";
import type { DealPayload, Client } from "../../types";

type DealFormProps = {
  clients: Client[];
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

export default function DealForm({
  clients,
  onSubmit,
  isLoading = false,
}: DealFormProps) {
  const [clientId, setClientId] = useState<number | "">("");
  const [dealName, setDealName] = useState("");
  const [industry, setIndustry] = useState("");
  const [dealValue, setDealValue] = useState("");
  const [termMonths, setTermMonths] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (clientId === "") {
      return;
    }

    onSubmit({
      name: dealName.trim(),
      value: Number(dealValue),
      term_months: Number(termMonths),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">Create Deal</h2>
      <p className="deal-form__subtitle">
        Submit a new deal for an existing client
      </p>

      <fieldset className="deal-form__section" disabled={isLoading}>
        <legend className="deal-form__section-title">
          Deal Information
        </legend>

        <label className="deal-form__field">
          <span className="deal-form__label">
            Client
          </span>

          <select
            className="deal-form__input"
            value={clientId}
            onChange={(e) => setClientId(Number(e.target.value))}
            required
          >
            <option value="">
              Select a client
            </option>

            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.name}
              </option>
            ))}
          </select>
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">
            Deal Name
          </span>

          <input
            className="deal-form__input"
            type="text"
            value={dealName}
            onChange={(e) => setDealName(e.target.value)}
            placeholder="e.g. Working Capital Facility"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">
            Industry
          </span>

          <select
            className="deal-form__input"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
          >
            <option value="">
              Select an industry
            </option>

            {INDUSTRIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">
            Deal Value (USD)
          </span>

          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={dealValue}
            onChange={(e) => setDealValue(e.target.value)}
            placeholder="e.g. 1500000"
            required
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">
            Term (months)
          </span>

          <input
            className="deal-form__input"
            type="number"
            min="1"
            step="1"
            value={termMonths}
            onChange={(e) => setTermMonths(e.target.value)}
            placeholder="e.g. 12"
            required
          />
        </label>
      </fieldset>

      <button
        className="deal-form__submit"
        type="submit"
        disabled={isLoading}
      >
        {isLoading ? "Submitting…" : "Submit Deal"}
      </button>
    </form>
  );
}
