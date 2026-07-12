import { useEffect, useState } from "react";
import { evaluateDeal } from "../services/dealService";
import { getClients } from "../services/clientService";
import type { Client, DealPayload } from "../types";

export default function DealPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState("");
  const [dealName, setDealName] = useState("");
  const [loanAmount, setLoanAmount] = useState("");

  const [isLoadingClients, setIsLoadingClients] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadClients() {
      setIsLoadingClients(true);

      try {
        const data = await getClients();
        setClients(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load clients",
        );
      } finally {
        setIsLoadingClients(false);
      }
    }

    loadClients();
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    const selectedClient = clients.find(
      (client) => client.id === Number(clientId),
    );

    if (!selectedClient) {
      setError("Please select a valid client");
      setIsSubmitting(false);
      return;
    }

    const payload: DealPayload = {
      client_id: selectedClient.id,
      name: dealName.trim(),
      industry: selectedClient.industry,
      value: Number(loanAmount),
    };

    try {
      await evaluateDeal(payload);

      setMessage(
        "Deal submitted successfully. It is pending approval.",
      );

      setDealName("");
      setLoanAmount("");
      setClientId("");
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
          Submit a loan request for an existing client
        </p>

        <fieldset
          className="deal-form__section"
          disabled={isSubmitting}
        >
          <label className="deal-form__field">
            <span className="deal-form__label">
              Client
            </span>

            <select
              className="deal-form__input"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              required
              disabled={isLoadingClients}
            >
              <option value="">
                {isLoadingClients
                  ? "Loading clients..."
                  : "Select client"}
              </option>

              {clients.map((client) => (
                <option
                  key={client.id}
                  value={client.id}
                >
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