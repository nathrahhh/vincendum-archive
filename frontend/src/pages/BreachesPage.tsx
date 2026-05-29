import { useEffect, useState } from "react";
import { BreachesList } from "../components/risk";
import { getBreaches } from "../services/riskService";
import type { BreachesByIndustry } from "../types";

export default function BreachesPage() {
  const [breaches, setBreaches] = useState<BreachesByIndustry>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getBreaches();
        if (!cancelled) {
          setBreaches(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load breaches");
          setBreaches({});
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="breaches-page">
      {isLoading ? <p className="breaches-page__status">Loading breaches…</p> : null}
      {error ? <p className="dashboard-error">{error}</p> : null}
      {!isLoading && !error ? <BreachesList breaches={breaches} /> : null}
    </div>
  );
}
