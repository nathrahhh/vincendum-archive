import type { ClientFinancials, ClientForecast } from "../../types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type RevenueScenarioChartProps = {
  financials: ClientFinancials | null;
  baseForecast: ClientForecast | null;
  bestForecast: ClientForecast | null;
  worstForecast: ClientForecast | null;
};

type ChartPoint = {
  month: string;
  historical: number | null;
  base: number | null;
  best: number | null;
  worst: number | null;
};

function buildChartData(
  financials: ClientFinancials,
  baseForecast: ClientForecast,
  bestForecast: ClientForecast,
  worstForecast: ClientForecast,
): ChartPoint[] {
  const historical = financials.historical ?? [];
  const base = baseForecast.forecast ?? [];
  const best = bestForecast.forecast ?? [];
  const worst = worstForecast.forecast ?? [];

  if (
    historical.length === 0 &&
    base.length === 0 &&
    best.length === 0 &&
    worst.length === 0
  ) {
    return [];
  }

  const data: ChartPoint[] = historical.map((record) => ({
    month: record.month.slice(0, 7),
    historical: record.revenue,
    base: null,
    best: null,
    worst: null,
  }));

  const lastHistoricalIndex = historical.length - 1;
  if (lastHistoricalIndex >= 0) {
    const lastRevenue = historical[lastHistoricalIndex].revenue;
    data[lastHistoricalIndex].base = lastRevenue;
    data[lastHistoricalIndex].best = lastRevenue;
    data[lastHistoricalIndex].worst = lastRevenue;
  }

  const lastHistoricalMonth = data[lastHistoricalIndex]?.month;

  function mergeScenario(
    records: { month: string; revenue: number }[],
    key: "base" | "best" | "worst",
  ) {
    for (const record of records) {
      const month = record.month.slice(0, 7);
      if (month === lastHistoricalMonth) {
        continue;
      }
      const existingIndex = data.findIndex((point) => point.month === month);
      if (existingIndex >= 0) {
        data[existingIndex][key] = record.revenue;
      } else {
        data.push({
          month,
          historical: null,
          base: key === "base" ? record.revenue : null,
          best: key === "best" ? record.revenue : null,
          worst: key === "worst" ? record.revenue : null,
        });
      }
    }
  }

  mergeScenario(base, "base");
  mergeScenario(best, "best");
  mergeScenario(worst, "worst");

  return data;
}

export default function RevenueScenarioChart({
  financials,
  baseForecast,
  bestForecast,
  worstForecast,
}: RevenueScenarioChartProps) {
  if (!financials || !baseForecast || !bestForecast || !worstForecast) {
    return (
      <p className="clients-panel__hint">Select a client to view revenue scenarios.</p>
    );
  }

  const data = buildChartData(financials, baseForecast, bestForecast, worstForecast);

  if (data.length === 0) {
    return <p className="clients-panel__hint">No revenue scenario data available.</p>;
  }

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="historical"
            name="Historical revenue"
            stroke="#4f46e5"
            strokeWidth={2}
            dot
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="base"
            name="Base forecast"
            stroke="#059669"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="best"
            name="Best case"
            stroke="#2563eb"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="worst"
            name="Worst case"
            stroke="#dc2626"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
