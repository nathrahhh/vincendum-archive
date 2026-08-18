import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ClientApplicationForm from "../components/clients/ClientApplicationForm";
import { submitClientApplication } from "../services/clientService";
import { fetchPublicLender } from "../services/lenderService";
import type { Lender } from "../types/auth";
import type { ClientApplicationCreate } from "../types";

function optionalTrimmed(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed === "" ? undefined : trimmed;
}

function optionalNumber(value: string): number | undefined {
  const trimmed = value.trim();
  if (trimmed === "") {
    return undefined;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export default function ApplyPage() {
  const { lenderSlug } = useParams<{ lenderSlug: string }>();

  const [lender, setLender] = useState<Lender | null>(null);
  const [isLoadingLender, setIsLoadingLender] = useState(true);
  const [lenderError, setLenderError] = useState<string | null>(null);

  const [businessName, setBusinessName] = useState("");
  const [registeredBusinessName, setRegisteredBusinessName] = useState("");
  const [industry, setIndustry] = useState("");
  const [companiesHouseNumber, setCompaniesHouseNumber] = useState("");
  const [incorporationYear, setIncorporationYear] = useState("");
  const [headcount, setHeadcount] = useState("");
  const [revenueLastFy, setRevenueLastFy] = useState("");
  const [creditLimit, setCreditLimit] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [reasons, setReasons] = useState<string[]>([]);
  const [isRejection, setIsRejection] = useState(false);

  useEffect(() => {
    if (!lenderSlug) {
      setLender(null);
      setIsLoadingLender(false);
      setLenderError("This application link is missing a lender.");
      return;
    }

    const slug = lenderSlug;
    let cancelled = false;

    async function loadLender() {
      setIsLoadingLender(true);
      setLenderError(null);
      setLender(null);

      try {
        const resolved = await fetchPublicLender(slug);
        if (!cancelled) {
          setLender(resolved);
        }
      } catch (err) {
        if (!cancelled) {
          setLenderError(
            err instanceof Error
              ? err.message
              : "Failed to load lender",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingLender(false);
        }
      }
    }

    void loadLender();

    return () => {
      cancelled = true;
    };
  }, [lenderSlug]);

  function resetFormFields() {
    setBusinessName("");
    setRegisteredBusinessName("");
    setIndustry("");
    setCompaniesHouseNumber("");
    setIncorporationYear("");
    setHeadcount("");
    setRevenueLastFy("");
    setCreditLimit("");
  }

  async function handleSubmit() {
    const payload: ClientApplicationCreate = {
      name: businessName.trim(),
      industry: industry.trim(),
      credit_limit: Number(creditLimit),
      registered_business_name: optionalTrimmed(registeredBusinessName),
      companies_house_number: optionalTrimmed(companiesHouseNumber),
      incorporation_year: optionalNumber(incorporationYear),
      headcount: optionalNumber(headcount),
      revenue_last_fy: optionalNumber(revenueLastFy),
    };

    setIsSubmitting(true);
    setError(null);
    setMessage(null);
    setReasons([]);
    setIsRejection(false);

    try {
      const response = await submitClientApplication(payload);

      const rejected = response.application?.status === "rejected";

      setIsRejection(rejected);

      if (rejected) {
        setMessage(response.message);
      } else {
        setMessage("Application received. It is pending review.");
        resetFormFields();
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

  if (isLoadingLender) {
    return (
      <div className="client-financials-page">
        <p className="dashboard-panel__subtitle">Loading lender…</p>
      </div>
    );
  }

  if (lenderError || !lender) {
    return (
      <div className="client-financials-page">
        <p className="dashboard-error">
          {lenderError ?? "Lender not found"}
        </p>
      </div>
    );
  }

  return (
    <div className="client-financials-page">
      <h1 className="deal-form__title">Apply to {lender.name}</h1>

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
        registeredBusinessName={registeredBusinessName}
        industry={industry}
        companiesHouseNumber={companiesHouseNumber}
        incorporationYear={incorporationYear}
        headcount={headcount}
        revenueLastFy={revenueLastFy}
        creditLimit={creditLimit}
        isSubmitting={isSubmitting}
        onBusinessNameChange={setBusinessName}
        onRegisteredBusinessNameChange={setRegisteredBusinessName}
        onIndustryChange={setIndustry}
        onCompaniesHouseNumberChange={setCompaniesHouseNumber}
        onIncorporationYearChange={setIncorporationYear}
        onHeadcountChange={setHeadcount}
        onRevenueLastFyChange={setRevenueLastFy}
        onCreditLimitChange={setCreditLimit}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
