import type { ForecastRevenuePoint } from "../../types/clients";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type RecommendedForecastChartProps = {
  historical: ForecastRevenuePoint[];
  forecast: ForecastRevenuePoint[];
};

type ChartPoint = {
  month: string;
  historicalRevenue: number | null;
  forecastRevenue: number | null;
};

function buildChartData(
  historical: ForecastRevenuePoint[],
  forecast: ForecastRevenuePoint[],
): ChartPoint[] {
  const byMonth = new Map<string, ChartPoint>();

  for (const point of historical) {
    const month = point.month.slice(0, 7);
    byMonth.set(month, {
      month,
      historicalRevenue: point.revenue,
      forecastRevenue: null,
    });
  }

  // Bridge the last historical point into the forecast series for continuity.
  if (historical.length > 0) {
    const last = historical[historical.length - 1];
    const month = last.month.slice(0, 7);
    const existing = byMonth.get(month);
    if (existing) {
      existing.forecastRevenue = last.revenue;
    }
  }

  for (const point of forecast) {
    const month = point.month.slice(0, 7);
    const existing = byMonth.get(month);
    if (existing) {
      existing.forecastRevenue = point.revenue;
    } else {
      byMonth.set(month, {
        month,
        historicalRevenue: null,
        forecastRevenue: point.revenue,
      });
    }
  }

  return Array.from(byMonth.values()).sort((a, b) =>
    a.month.localeCompare(b.month),
  );
}

export default function RecommendedForecastChart({
  historical,
  forecast,
}: RecommendedForecastChartProps) {
  const data = buildChartData(historical, forecast);

  if (data.length === 0) {
    return (
      <p className="clients-panel__hint">No forecast data available.</p>
    );
  }

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip
            formatter={(value) =>
              typeof value === "number"
                ? new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                    maximumFractionDigits: 0,
                  }).format(value)
                : value
            }
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="historicalRevenue"
            name="Historical Revenue"
            stroke="#4f46e5"
            strokeWidth={2}
            dot
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="forecastRevenue"
            name="Forecast Revenue"
            stroke="#059669"
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
