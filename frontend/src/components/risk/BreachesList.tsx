import type { BreachesByIndustry } from "../../types";

type BreachesListProps = {
  breaches: BreachesByIndustry;
};

export default function BreachesList({ breaches }: BreachesListProps) {
  const industries = Object.keys(breaches).sort();

  if (industries.length === 0) {
    return <p className="breaches-empty">No breaches recorded.</p>;
  }

  return (
    <div className="breaches-list">
      {industries.map((industry) => (
        <section key={industry} className="breaches-group">
          <h3 className="breaches-group__title">{industry}</h3>
          <ul className="breaches-group__items">
            {breaches[industry].map((breach) => (
              <li key={breach.id ?? `${breach.rule}-${breach.detail}`} className="breaches-item">
                <p className="breaches-item__rule">{breach.rule}</p>
                <p className="breaches-item__metrics">
                  Limit: {breach.limit_pct} · Actual: {breach.actual_pct}
                </p>
                <p className="breaches-item__detail">{breach.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
