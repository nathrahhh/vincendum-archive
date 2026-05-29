type KpiCardProps = {
  label: string;
  value: string;
  hint?: string;
};

export default function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <article className="dashboard-kpi">
      <p className="dashboard-kpi__label">{label}</p>
      <p className="dashboard-kpi__value">{value}</p>
      {hint ? <p className="dashboard-kpi__hint">{hint}</p> : null}
    </article>
  );
}
