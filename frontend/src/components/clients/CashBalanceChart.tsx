import type { ClientFinancials, ClientForecast } from "../../types";

type CashBalanceChartProps = {
  financials: ClientFinancials | null;
  forecast: ClientForecast | null;
};

const WIDTH = 480;
const HEIGHT = 220;
const PADDING = 40;

function toPoints(values: number[], startIndex: number, total: number, minY: number, maxY: number) {
  const range = maxY - minY || 1;
  return values
    .map((value, index) => {
      const x = PADDING + ((startIndex + index) / Math.max(total - 1, 1)) * (WIDTH - PADDING * 2);
      const y = HEIGHT - PADDING - ((value - minY) / range) * (HEIGHT - PADDING * 2);
      return `${x},${y}`;
    })
    .join(" ");
}

export default function CashBalanceChart({ financials, forecast }: CashBalanceChartProps) {
  if (!financials || !forecast) {
    return <p className="clients-panel__hint">Select a client to view cash balance chart.</p>;
  }

  const labels = [...financials.labels, ...forecast.forecast.labels];
  const historical = financials.cash_balance;
  const forecastValues = forecast.forecast.cash_balance;

  if (labels.length === 0) {
    return <p className="clients-panel__hint">No financial data available.</p>;
  }

  const allValues = [...historical, ...forecastValues];
  const minY = Math.min(...allValues);
  const maxY = Math.max(...allValues);
  const historicalPoints = toPoints(historical, 0, labels.length, minY, maxY);
  const forecastPoints = toPoints(
    forecastValues,
    historical.length,
    labels.length,
    minY,
    maxY,
  );

  return (
    <div className="clients-chart">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="clients-chart__svg" role="img">
        <polyline points={historicalPoints} fill="none" stroke="#4f46e5" strokeWidth="2" />
        <polyline
          points={forecastPoints}
          fill="none"
          stroke="#059669"
          strokeWidth="2"
          strokeDasharray="6 4"
        />
      </svg>
      <div className="clients-chart__legend">
        <span className="clients-chart__legend-item clients-chart__legend-item--historical">
          Historical cash balance
        </span>
        <span className="clients-chart__legend-item clients-chart__legend-item--forecast">
          Forecast cash balance
        </span>
      </div>
      <div className="clients-chart__labels">
        {labels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
    </div>
  );
}
