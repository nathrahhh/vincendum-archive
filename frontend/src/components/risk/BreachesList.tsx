import { useEffect, useState } from "react";
import { resolveBreach } from "../../services/riskService";
import type { BreachRecord, BreachesByIndustry } from "../../types";

type BreachesListProps = {
  breaches: BreachesByIndustry;
};

export default function BreachesList({ breaches }: BreachesListProps) {
  const [items, setItems] = useState<BreachesByIndustry>(breaches);
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [errors, setErrors] = useState<Record<number, string>>({});

  useEffect(() => {
    setItems(breaches);
    setErrors({});
  }, [breaches]);

  const industries = Object.keys(items).sort();

  if (industries.length === 0) {
    return <p className="breaches-empty">No breaches recorded.</p>;
  }

  async function handleResolve(breach: BreachRecord) {
    if (resolvingId !== null) {
      return;
    }

    setResolvingId(breach.id);
    setErrors((prev) => {
      const next = { ...prev };
      delete next[breach.id];
      return next;
    });

    try {
      const updated = await resolveBreach(breach.id);
      setItems((prev) => {
        const next: BreachesByIndustry = {};
        for (const [industry, list] of Object.entries(prev)) {
          next[industry] = list.map((row) =>
            row.id === updated.id ? { ...row, ...updated } : row,
          );
        }
        return next;
      });
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        [breach.id]:
          err instanceof Error ? err.message : "Failed to resolve breach",
      }));
    } finally {
      setResolvingId(null);
    }
  }

  return (
    <div className="breaches-list">
      {industries.map((industry) => (
        <section key={industry} className="breaches-group">
          <h3 className="breaches-group__title">{industry}</h3>
          <ul className="breaches-group__items">
            {items[industry].map((breach) => {
              const isResolving = resolvingId === breach.id;
              return (
                <li key={breach.id} className="breaches-item">
                  <p className="breaches-item__rule">{breach.rule}</p>
                  <p className="breaches-item__metrics">
                    Threshold: {breach.threshold} · Actual: {breach.actual_value}
                  </p>
                  <p className="breaches-item__detail">{breach.detail}</p>
                  <p className="breaches-item__status">Status: {breach.status}</p>
                  {errors[breach.id] ? (
                    <p className="dashboard-error">{errors[breach.id]}</p>
                  ) : null}
                  {breach.status === "OPEN" ? (
                    <button
                      type="button"
                      className="breaches-item__resolve"
                      disabled={resolvingId !== null}
                      onClick={() => handleResolve(breach)}
                    >
                      {isResolving ? "Resolving…" : "Resolve"}
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
