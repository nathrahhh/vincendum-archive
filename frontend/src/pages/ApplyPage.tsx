import { useEffect, useState, type ChangeEvent } from "react";
import { useParams } from "react-router-dom";
import ClientApplicationForm from "../components/clients/ClientApplicationForm";
import {
  postClientApplication,
  requestApplicationDocumentUploadUrl,
} from "../services/clientApplicationService";
import { fetchPublicLender } from "../services/lenderService";
import type { Lender } from "../types/auth";
import type { ClientApplicationCreate } from "../types";

type UploadStatus = "idle" | "uploading" | "uploaded" | "error";

type StatementKey = "profitAndLoss" | "balanceSheet" | "cashFlow";

const STATEMENT_LABELS: Record<StatementKey, string> = {
  profitAndLoss: "Profit & Loss Statement",
  balanceSheet: "Balance Sheet",
  cashFlow: "Cash Flow Statement",
};

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

function emptyUploadStatus(): Record<StatementKey, UploadStatus> {
  return {
    profitAndLoss: "idle",
    balanceSheet: "idle",
    cashFlow: "idle",
  };
}

function emptyUploadErrors(): Record<StatementKey, string | null> {
  return {
    profitAndLoss: null,
    balanceSheet: null,
    cashFlow: null,
  };
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
  const [createdApplicationId, setCreatedApplicationId] = useState<number | null>(
    null,
  );

  const [selectedFiles, setSelectedFiles] = useState<
    Record<StatementKey, File | null>
  >({
    profitAndLoss: null,
    balanceSheet: null,
    cashFlow: null,
  });
  const [uploadStatus, setUploadStatus] = useState(emptyUploadStatus);
  const [uploadErrors, setUploadErrors] = useState(emptyUploadErrors);

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

    if (!lenderSlug) {
      setError("Lender context is missing. Please use a valid application link.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setMessage(null);
    setReasons([]);
    setIsRejection(false);

    try {
      const response = await postClientApplication(lenderSlug, payload);

      const rejected = response.application?.status === "rejected";

      setIsRejection(rejected);

      if (rejected) {
        setMessage(response.message);
        setCreatedApplicationId(null);
      } else {
        const applicationId = response.application?.id ?? null;
        if (applicationId == null) {
          setError("Application was created but no application ID was returned.");
          setCreatedApplicationId(null);
          return;
        }

        setCreatedApplicationId(applicationId);
        setMessage(
          "Application received. It is pending review. You can upload supporting PDFs below.",
        );
        resetFormFields();
        setSelectedFiles({
          profitAndLoss: null,
          balanceSheet: null,
          cashFlow: null,
        });
        setUploadStatus(emptyUploadStatus());
        setUploadErrors(emptyUploadErrors());
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

  function handleFileChange(
    key: StatementKey,
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0] ?? null;
    if (file && file.type !== "application/pdf") {
      setSelectedFiles((current) => ({ ...current, [key]: null }));
      setUploadStatus((current) => ({ ...current, [key]: "error" }));
      setUploadErrors((current) => ({
        ...current,
        [key]: "Only PDF files are allowed.",
      }));
      event.target.value = "";
      return;
    }

    setSelectedFiles((current) => ({ ...current, [key]: file }));
    setUploadStatus((current) => ({
      ...current,
      [key]: file ? "idle" : "idle",
    }));
    setUploadErrors((current) => ({ ...current, [key]: null }));
  }

  async function handleUpload(key: StatementKey) {
    if (!lenderSlug || createdApplicationId == null) {
      setUploadErrors((current) => ({
        ...current,
        [key]: "Application must be created before uploading documents.",
      }));
      return;
    }

    const file = selectedFiles[key];
    if (!file) {
      setUploadErrors((current) => ({
        ...current,
        [key]: "Select a PDF file first.",
      }));
      return;
    }

    if (file.type !== "application/pdf") {
      setUploadStatus((current) => ({ ...current, [key]: "error" }));
      setUploadErrors((current) => ({
        ...current,
        [key]: "Only PDF files are allowed.",
      }));
      return;
    }

    setUploadStatus((current) => ({ ...current, [key]: "uploading" }));
    setUploadErrors((current) => ({ ...current, [key]: null }));

    try {
      const contentType = file.type || "application/pdf";
      const prepared = await requestApplicationDocumentUploadUrl(
        lenderSlug,
        createdApplicationId,
        {
          name: STATEMENT_LABELS[key],
          content_type: contentType,
        },
      );

      const uploadResponse = await fetch(prepared.upload_url, {
        method: "PUT",
        headers: {
          "Content-Type": contentType,
        },
        body: file,
      });

      if (!uploadResponse.ok) {
        throw new Error(
          `S3 upload failed (${uploadResponse.status} ${uploadResponse.statusText})`,
        );
      }

      setUploadStatus((current) => ({ ...current, [key]: "uploaded" }));
    } catch (err) {
      setUploadStatus((current) => ({ ...current, [key]: "error" }));
      setUploadErrors((current) => ({
        ...current,
        [key]:
          err instanceof Error ? err.message : "Failed to upload document",
      }));
    }
  }

  function uploadStatusLabel(status: UploadStatus): string {
    if (status === "uploading") {
      return "Uploading…";
    }
    if (status === "uploaded") {
      return "Uploaded";
    }
    return "";
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

      {createdApplicationId != null ? (
        <section className="deal-form" style={{ marginTop: "1.5rem" }}>
          <h2 className="deal-form__title">Supporting documents</h2>
          <p className="deal-form__subtitle">
            Upload PDF statements for this application. Documents are optional
            and are sent directly to secure storage.
          </p>

          <fieldset className="deal-form__section">
            <legend className="deal-form__section-title">
              Financial statements
            </legend>

            {(Object.keys(STATEMENT_LABELS) as StatementKey[]).map((key) => (
              <label key={key} className="deal-form__field">
                <span className="deal-form__label">{STATEMENT_LABELS[key]}</span>
                <input
                  className="deal-form__input"
                  type="file"
                  accept="application/pdf,.pdf"
                  disabled={uploadStatus[key] === "uploading"}
                  onChange={(event) => handleFileChange(key, event)}
                />
                <button
                  className="deal-form__submit"
                  type="button"
                  disabled={
                    !selectedFiles[key] ||
                    uploadStatus[key] === "uploading" ||
                    uploadStatus[key] === "uploaded"
                  }
                  onClick={() => {
                    void handleUpload(key);
                  }}
                >
                  {uploadStatus[key] === "uploading"
                    ? "Uploading…"
                    : uploadStatus[key] === "uploaded"
                      ? "Uploaded"
                      : "Upload PDF"}
                </button>
                {uploadStatusLabel(uploadStatus[key]) ? (
                  <p className="dashboard-panel__subtitle">
                    {uploadStatusLabel(uploadStatus[key])}
                  </p>
                ) : null}
                {uploadErrors[key] ? (
                  <p className="dashboard-error">{uploadErrors[key]}</p>
                ) : null}
              </label>
            ))}
          </fieldset>
        </section>
      ) : null}
    </div>
  );
}
