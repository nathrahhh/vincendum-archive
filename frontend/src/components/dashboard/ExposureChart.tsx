import type { IndustryExposure } from "../../types";

type ExposureChartProps = {
  exposure: IndustryExposure[];
  isLoading?: boolean;
};

export default function ExposureChart({ exposure, isLoading }: ExposureChartProps) {
  const maxPct = exposure.length > 0 ? Math.max(...exposure.map((e) => e.percentage)) : 0;

  return (
    <section className="dashboard-panel">
      <h2 className="dashboard-panel__title">Industry Exposure</h2>
      {isLoading ? <p className="dashboard-panel__subtitle">Loading exposure…</p> : null}
      {!isLoading && exposure.length === 0 ? (
        <p className="dashboard-panel__subtitle">No industry exposure data.</p>
      ) : null}
      {!isLoading && exposure.length > 0 ? (
        <div className="dashboard-chart">
          {exposure.map((item) => (
            <div key={item.industry} className="dashboard-chart__row">
              <span className="dashboard-chart__label">{item.industry}</span>
              <div className="dashboard-chart__bar-track">
                <div
                  className="dashboard-chart__bar"
                  style={{ width: `${maxPct > 0 ? (item.percentage / maxPct) * 100 : 0}%` }}
                />
              </div>
              <span className="dashboard-chart__value">{item.percentage.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
