
import { useState } from "react";
import ClientApplicationForm from "../components/clients/ClientApplicationForm";
import { submitClientApplication } from "../services/clientService";
import type { ClientApplicationCreate } from "../types";

export default function ApplyPage() {
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("");
  const [creditLimit, setCreditLimit] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [reasons, setReasons] = useState<string[]>([]);
  const [isRejection, setIsRejection] = useState(false);

  async function handleSubmit(payload: ClientApplicationCreate) {
    setIsSubmitting(true);
    setError(null);
    setMessage(null);
    setReasons([]);
    setIsRejection(false);

    try {
      const response = await submitClientApplication(payload);

      const rejected =
        Boolean(response.reasons?.length) ||
        response.application?.status === "rejected";

      setIsRejection(rejected);

      if (rejected) {
        setMessage(response.message);
        setReasons(response.reasons ?? []);
      } else {
        setMessage("Application received. It is pending review.");

        setBusinessName("");
        setIndustry("");
        setCreditLimit("");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to submit application",
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

      {message && !isRejection ? (
        <p className="client-financials__success">
          {message}
        </p>
      ) : null}

      {message && isRejection ? (
        <p className="client-apply__rejection">
          {message}
        </p>
      ) : null}

      {reasons.length > 0 ? (
        <div className="client-apply__reasons">
          <h3 className="deal-result-panel__breaches-title">
            Rejection reasons
          </h3>

          <ul className="deal-result-panel__breach-list">
            {reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <ClientApplicationForm
        businessName={businessName}
        industry={industry}
        creditLimit={creditLimit}
        isSubmitting={isSubmitting}
        onBusinessNameChange={setBusinessName}
        onIndustryChange={setIndustry}
        onCreditLimitChange={setCreditLimit}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
