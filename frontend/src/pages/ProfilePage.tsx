import { useCallback, useEffect, useState } from "react";
import { fetchMyLender } from "../services/lenderService";
import type { Lender } from "../types/auth";

export default function ProfilePage() {
  const [lender, setLender] = useState<Lender | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLender = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchMyLender();
      setLender(data);
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