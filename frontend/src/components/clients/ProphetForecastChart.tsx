import type { ProphetForecastRecord, ProphetHistoricalRecord } from "../../types/clients";
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

type ProphetForecastChartProps = {
  historical: ProphetHistoricalRecord[];
  forecast: ProphetForecastRecord[];
};

type ChartPoint = {
  month: string;
  historical: number | null;
  prophetRevenue: number | null;
  base: number | null;
  best: number | null;
  worst: number | null;
  lowerBound: number | null;
  upperBound: number | null;
};

function buildChartData(
  historical: ProphetHistoricalRecord[],
  forecast: ProphetForecastRecord[],
): ChartPoint[] {
  if (historical.length === 0 && forecast.length === 0) {
    return [];
  }

  const data: ChartPoint[] = historical.map((record) => ({
    month: record.month.slice(0, 7),
    historical: record.revenue,
    prophetRevenue: null,
    base: null,
    best: null,
    worst: null,
    lowerBound: null,
    upperBound: null,
  }));

  const lastHistoricalIndex = historical.length - 1;
  if (lastHistoricalIndex >= 0) {
    const lastRevenue = historical[lastHistoricalIndex].revenue;
    data[lastHistoricalIndex].prophetRevenue = lastRevenue;
    data[lastHistoricalIndex].base = lastRevenue;
    data[lastHistoricalIndex].best = lastRevenue;
    data[lastHistoricalIndex].worst = lastRevenue;
    data[lastHistoricalIndex].lowerBound = lastRevenue;
    data[lastHistoricalIndex].upperBound = lastRevenue;
  }

  const lastHistoricalMonth = data[lastHistoricalIndex]?.month;

  for (const record of forecast) {
    const month = record.month.slice(0, 7);
    if (month === lastHistoricalMonth) {
      continue;
    }

    const existingIndex = data.findIndex((point) => point.month === month);
    if (existingIndex >= 0) {
      data[existingIndex].prophetRevenue = record.revenue;
      data[existingIndex].base = record.base;
      data[existingIndex].best = record.best;
      data[existingIndex].worst = record.worst;
      data[existingIndex].lowerBound = record.lower_bound;
      data[existingIndex].upperBound = record.upper_bound;
    } else {
      data.push({
        month,
        historical: null,
        prophetRevenue: record.revenue,
        base: record.base,
        best: record.best,
        worst: record.worst,
        lowerBound: record.lower_bound,
        upperBound: record.upper_bound,
      });
    }
  }

  return data;
}

export default function ProphetForecastChart({
  historical,
  forecast,
}: ProphetForecastChartProps) {
  const data = buildChartData(historical ?? [], forecast ?? []);

  if (data.length === 0) {
    return <p className="clients-panel__hint">No Prophet forecast data available.</p>;
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
            dataKey="prophetRevenue"
            name="Prophet revenue"
            stroke="#059669"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="base"
            name="Base"
            stroke="#0d9488"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="best"
            name="Best"
            stroke="#2563eb"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="worst"
            name="Worst"
            stroke="#dc2626"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="lowerBound"
            name="Lower bound"
            stroke="#9ca3af"
            strokeWidth={1.5}
            strokeDasharray="2 4"
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="upperBound"
            name="Upper bound"
            stroke="#9ca3af"
            strokeWidth={1.5}
            strokeDasharray="2 4"
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
