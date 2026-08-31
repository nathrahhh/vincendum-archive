import { useState } from "react";
import { createMyDeal } from "../services/dealService";
import type { DealPayload } from "../types";

export default function DealPage() {
  const [dealName, setDealName] = useState("");
  const [loanAmount, setLoanAmount] = useState("");
  const [termMonths, setTermMonths] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    const payload: DealPayload = {
      name: dealName.trim(),
      value: Number(loanAmount),
      term_months: Number(termMonths),
    };

    try {
      await createMyDeal(payload);

      setMessage(
        "Deal submitted successfully. It is pending approval.",
      );

      setDealName("");
      setLoanAmount("");
      setTermMonths("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit deal",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="client-financials-page">
      {error ? (
        <p className="dashboard-error">{error}</p>
      ) : null}

      {message ? (
        <p className="client-financials__success">{message}</p>
      ) : null}

      <form className="deal-form" onSubmit={handleSubmit}>
        <h2 className="deal-form__title">
          Deal Application
        </h2>

        <p className="deal-form__subtitle">
          Submit a loan request
        </p>

        <fieldset
          className="deal-form__section"
          disabled={isSubmitting}
        >
          <label className="deal-form__field">
            <span className="deal-form__label">
              Deal Name
            </span>

            <input
              className="deal-form__input"
              type="text"
              value={dealName}
              onChange={(e) =>
                setDealName(e.target.value)
              }
              placeholder="e.g. Expansion Facility"
              required
            />
          </label>


          <label className="deal-form__field">
            <span className="deal-form__label">
              Requested Loan Amount (USD)
            </span>

            <input
              className="deal-form__input"
              type="number"
              min="0"
              value={loanAmount}
              onChange={(e) =>
                setLoanAmount(e.target.value)
              }
              placeholder="e.g. 500000"
              required
            />
          </label>

          <label className="deal-form__field">
            <span className="deal-form__label">
              Requested Term (months)
            </span>

            <input
              className="deal-form__input"
              type="number"
              min="1"
              step="1"
              value={termMonths}
              onChange={(e) =>
                setTermMonths(e.target.value)
              }
              placeholder="e.g. 12"
              required
            />
          </label>
        </fieldset>


        <button
          className="deal-form__submit"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Submitting..."
            : "Submit Deal"}
        </button>
      </form>
    </div>
  );
}
