const mockExposure = [
  { industry: "Technology", pct: 28.8 },
  { industry: "Manufacturing", pct: 22.5 },
  { industry: "Healthcare", pct: 18.9 },
  { industry: "Retail", pct: 16.2 },
  { industry: "Energy", pct: 13.5 },
];

export default function ExposureChartPlaceholder() {
  const maxPct = Math.max(...mockExposure.map((e) => e.pct));

  return (
    <section className="dashboard-panel">
      <h2 className="dashboard-panel__title">Industry Exposure</h2>
      <p className="dashboard-panel__subtitle">Placeholder chart — connect API later</p>
      <div className="dashboard-chart">
        {mockExposure.map((item) => (
          <div key={item.industry} className="dashboard-chart__row">
            <span className="dashboard-chart__label">{item.industry}</span>
            <div className="dashboard-chart__bar-track">
              <div
                className="dashboard-chart__bar"
                style={{ width: `${(item.pct / maxPct) * 100}%` }}
              />
            </div>
            <span className="dashboard-chart__value">{item.pct}%</span>
          </div>
        ))}
      </div>
    </section>
  );
}
