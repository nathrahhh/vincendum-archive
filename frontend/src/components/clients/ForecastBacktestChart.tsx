import type { ForecastBacktestResult } from "../../types/clients";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ForecastBacktestChartProps = {
  results: ForecastBacktestResult[];
  bestModel: string | null;
};

type ChartPoint = {
  model: string;
  displayName: string;
  mae: number;
  isBest: boolean;
};

const MODEL_DISPLAY_NAMES: Record<string, string> = {
  naive: "Naive",
  seasonal_naive: "Seasonal Naive",
  ets: "ETS",
  holt_winters: "Holt-Winters",
  prophet: "Prophet",
};

export function formatForecastModelName(model: string): string {
  return MODEL_DISPLAY_NAMES[model] ?? model;
}

function buildChartData(
  results: ForecastBacktestResult[],
  bestModel: string | null,
): ChartPoint[] {
  return results
    .filter((result) => result.available && result.mae != null)
    .map((result) => ({
      model: result.model,
      displayName: formatForecastModelName(result.model),
      mae: result.mae as number,
      isBest: result.model === bestModel,
    }));
}

export default function ForecastBacktestChart({
  results,
  bestModel,
}: ForecastBacktestChartProps) {
  const data = buildChartData(results, bestModel);

  if (data.length === 0) {
    return (
      <p className="clients-panel__hint">
        No model MAE results are available to chart.
      </p>
    );
  }

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="displayName" />
          <YAxis />
          <Tooltip
            formatter={(value) =>
              typeof value === "number"
                ? new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  }).format(value)
                : value
            }
          />
          <Bar dataKey="mae" name="MAE">
            {data.map((entry) => (
              <Cell
                key={entry.model}
                fill={entry.isBest ? "#059669" : "#4f46e5"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
