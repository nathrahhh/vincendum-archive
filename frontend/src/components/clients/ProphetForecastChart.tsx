import type {
  ProphetForecastPoint,
  ProphetHistoricalPoint,
} from "../../types/clients";

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
  historical?: ProphetHistoricalPoint[];
  forecast?: ProphetForecastPoint[];
};


export default function ProphetForecastChart({
  historical = [],
  forecast = [],
}: ProphetForecastChartProps) {

  const data = [
    ...historical.map((record) => ({
      month: record.month.slice(0, 7),
      revenue: record.revenue,
      lowerBound: null,
      upperBound: null,
      type: "historical",
    })),

    ...forecast.map((record) => ({
      month: record.month.slice(0, 7),
      revenue: record.revenue,
      lowerBound: record.lower_bound,
      upperBound: record.upper_bound,
      type: "forecast",
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
            dataKey="revenue"
            name="Revenue"
            stroke="#2563eb"
            strokeWidth={2}
            dot
            connectNulls
          />


          <Line
            type="monotone"
            dataKey="lowerBound"
            name="Lower confidence bound"
            stroke="#9ca3af"
            strokeWidth={1}
            strokeDasharray="2 4"
            dot={false}
          />


          <Line
            type="monotone"
            dataKey="upperBound"
            name="Upper confidence bound"
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