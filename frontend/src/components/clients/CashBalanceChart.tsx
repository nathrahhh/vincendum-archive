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

type CashBalanceChartProps = {
  financials: ClientFinancials | null;
  forecast: ClientForecast | null;
};

type ChartPoint = {
  month: string;
  historical: number | null;
  forecast: number | null;
};

function buildChartData(
  historicalLabels: string[],
  historical: number[],
  forecastLabels: string[],
  forecastValues: number[],
): ChartPoint[] {
  if (historicalLabels.length === 0 && forecastLabels.length === 0) {
    return [];
  }

  const data: ChartPoint[] = historicalLabels.map((month, index) => ({
    month,
    historical: historical[index],
    forecast: null,
  }));

  const lastHistoricalIndex = historical.length - 1;
  if (lastHistoricalIndex >= 0) {
    data[lastHistoricalIndex].forecast = historical[lastHistoricalIndex];
  }

  const lastHistoricalMonth = historicalLabels[lastHistoricalIndex];

  for (let index = 0; index < forecastLabels.length; index++) {
    const month = forecastLabels[index];
    const value = forecastValues[index];
    const existingIndex = data.findIndex((point) => point.month === month);

    if (existingIndex >= 0 && month === lastHistoricalMonth) {
      continue;
    }

    if (existingIndex >= 0) {
      data[existingIndex].forecast = value;
    } else {
      data.push({
        month,
        historical: null,
        forecast: value,
      });
    }
  }

  return data;
}

export default function CashBalanceChart({ financials, forecast }: CashBalanceChartProps) {
  if (!financials || !forecast) {
    return (
      <p className="clients-panel__hint">Select a client to view cash balance chart.</p>
    );
  }

  const historical = financials.cash_balance;
  const forecastValues = forecast.forecast.cash_balance;
  const historicalLabels = financials.labels;
  const forecastLabels = forecast.forecast.labels;

  const data = buildChartData(
    historicalLabels,
    historical,
    forecastLabels,
    forecastValues,
  );

  if (data.length === 0) {
    return <p className="clients-panel__hint">No financial data available.</p>;
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
            name="Historical cash balance"
            stroke="#4f46e5"
            strokeWidth={2}
            dot
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast cash balance"
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
