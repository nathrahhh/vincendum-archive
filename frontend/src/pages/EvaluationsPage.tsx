import { useEffect, useState } from "react";
import { EvaluationsTable } from "../components/evaluations";
import { getDeals } from "../services/dealService";
import type { DealRecord } from "../types";

export default function EvaluationsPage() {
  const [deals, setDeals] = useState<DealRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDeals() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getDeals();
        if (!cancelled) {
          setDeals(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load deals");
          setDeals([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadDeals();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="evaluations-page">
      <EvaluationsTable deals={deals} isLoading={isLoading} error={error} />
    </div>
  );
}
