import type { ClientForecast } from "../../types";
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

type RevenueGrossProfitChartProps = {
  forecast: ClientForecast | null;
};

type ChartPoint = {
  month: string;
  historicalRevenue: number | null;
  historicalGrossProfit: number | null;
  forecastRevenue: number | null;
  forecastGrossProfit: number | null;
};

function buildChartData(forecast: ClientForecast): ChartPoint[] {
  const historical = forecast.historical ?? [];
  const projected = forecast.forecast ?? [];

  if (historical.length === 0 && projected.length === 0) {
    return [];
  }

  const data: ChartPoint[] = historical.map((record) => ({
    month: record.month,
    historicalRevenue: record.revenue,
    historicalGrossProfit: record.calculated_gross_profit,
    forecastRevenue: null,
    forecastGrossProfit: null,
  }));

  const lastHistoricalIndex = historical.length - 1;
  if (lastHistoricalIndex >= 0) {
    data[lastHistoricalIndex].forecastRevenue = historical[lastHistoricalIndex].revenue;
    data[lastHistoricalIndex].forecastGrossProfit =
      historical[lastHistoricalIndex].calculated_gross_profit;
  }

  const lastHistoricalMonth = historical[lastHistoricalIndex]?.month;

  for (const record of projected) {
    if (record.month === lastHistoricalMonth) {
      continue;
    }

    const existingIndex = data.findIndex((point) => point.month === record.month);
    if (existingIndex >= 0) {
      data[existingIndex].forecastRevenue = record.revenue;
      data[existingIndex].forecastGrossProfit = record.gross_profit_cogs_method;
    } else {
      data.push({
        month: record.month,
        historicalRevenue: null,
        historicalGrossProfit: null,
        forecastRevenue: record.revenue,
        forecastGrossProfit: record.gross_profit_cogs_method,
      });
    }
  }

  return data;
}

export default function RevenueGrossProfitChart({ forecast }: RevenueGrossProfitChartProps) {
  if (!forecast) {
    return (
      <p className="clients-panel__hint">Select a client to view revenue and gross profit chart.</p>
    );
  }

  const data = buildChartData(forecast);

  if (data.length === 0) {
    return <p className="clients-panel__hint">No revenue or gross profit data available.</p>;
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
            dataKey="historicalRevenue"
            name="Historical revenue"
            stroke="#4f46e5"
            strokeWidth={2}
            dot
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="historicalGrossProfit"
            name="Historical gross profit"
            stroke="#7c3aed"
            strokeWidth={2}
            dot
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="forecastRevenue"
            name="Forecast revenue"
            stroke="#059669"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="forecastGrossProfit"
            name="Forecast gross profit"
            stroke="#0d9488"
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
