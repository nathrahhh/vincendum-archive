import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  fetchMyLender,
  updateLenderCapitalBase,
} from "../services/lenderService";
import type { Lender } from "../types/auth";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ProfilePage() {
  const [lender, setLender] = useState<Lender | null>(null);
  const [capitalBase, setCapitalBase] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const loadLender = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchMyLender();
      setLender(data);
      setCapitalBase(String(data.capital_base));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load lender",
      );
      setLender(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLender();
  }, [loadLender]);

  async function handleCapitalBaseSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaveError(null);
    setIsSaving(true);
    try {
      const updated = await updateLenderCapitalBase(Number(capitalBase));
      setLender(updated);
      setCapitalBase(String(updated.capital_base));
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to update capital base",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        <h2 className="dashboard-panel__title">Profile</h2>

        {error ? (
          <p className="dashboard-error">{error}</p>
        ) : null}

        {isLoading ? (
          <p className="dashboard-panel__subtitle">
            Loading profile…
          </p>
        ) : null}

        {!isLoading && !error && lender ? (
          <>
            <p className="dashboard-panel__title">{lender.name}</p>

            <p className="dashboard-panel__subtitle">
              Current capital base: {formatCurrency(lender.capital_base)}
            </p>

            <form className="dashboard-form" onSubmit={handleCapitalBaseSubmit}>
              <label>
                Capital base
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={capitalBase}
                  onChange={(event) => setCapitalBase(event.target.value)}
                  required
                />
              </label>
              {saveError ? <p className="dashboard-error">{saveError}</p> : null}
              <button type="submit" disabled={isSaving}>
                {isSaving ? "Saving…" : "Update capital base"}
              </button>
            </form>

            <p className="dashboard-panel__subtitle">
              Public Application Link
            </p>
            <p>
              <a
                href={`${window.location.origin}/apply/${encodeURIComponent(
                  lender.slug,
                )}`}
                target="_blank"
                rel="noreferrer"
              >
                {`${window.location.origin}/apply/${encodeURIComponent(
                  lender.slug,
                )}`}
              </a>
            </p>
          </>
        ) : null}
      </section>
    </div>
  );
}
