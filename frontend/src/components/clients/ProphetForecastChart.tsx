import type { ProphetForecastPoint } from "../../types";

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


type HistoricalRevenuePoint = {
  month: string;
  revenue: number;
};


type ProphetForecastChartProps = {
  historical: HistoricalRevenuePoint[];
  forecast: ProphetForecastPoint[];
};


export default function ProphetForecastChart({
  historical,
  forecast,
}: ProphetForecastChartProps) {

  const data = [
    ...historical.map((record) => ({
      month: record.month.slice(0, 7),
      historicalRevenue: record.revenue,
      prophetRevenue: null,
      lowerBound: null,
      upperBound: null,
    })),

    ...forecast.map((record) => ({
      month: record.month.slice(0, 7),
      historicalRevenue: null,
      prophetRevenue: record.revenue,
      lowerBound: record.lower_bound,
      upperBound: record.upper_bound,
    })),
  ];


  if (data.length === 0) {
    return (
      <p className="clients-panel__hint">
        No Prophet forecast data available.
      </p>
    );
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
            stroke="#2563eb"
            strokeWidth={2}
            dot
          />


          <Line
            type="monotone"
            dataKey="prophetRevenue"
            name="Prophet forecast"
            stroke="#059669"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot
          />


          <Line
            type="monotone"
            dataKey="lowerBound"
            name="Lower bound"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="2 4"
            dot={false}
          />


          <Line
            type="monotone"
            dataKey="upperBound"
            name="Upper bound"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="2 4"
            dot={false}
          />

        </LineChart>

      </ResponsiveContainer>
    </div>
  );
}