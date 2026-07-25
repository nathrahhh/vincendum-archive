import { useEffect, useState } from "react";
import type {
  ClientFinancials,
  ClientForecast,
  ForecastModel,
  ProphetForecastResponse,
} from "../../types";
import { getClientForecast } from "../../services/clientService";
import ProphetForecastChart from "./ProphetForecastChart";
import RevenueGrossProfitChart from "./RevenueGrossProfitChart";
import RevenueScenarioChart from "./RevenueScenarioChart";

type ClientForecastTabProps = {
  clientId: number;
  financials: ClientFinancials | null;
  baseForecast: ClientForecast | null;
  bestForecast: ClientForecast | null;
  worstForecast: ClientForecast | null;
  baseGrowthRate: number;
  bestGrowthRate: number;
  worstGrowthRate: number;
  onBaseGrowthRateChange: (value: number) => void;
  onBestGrowthRateChange: (value: number) => void;
  onWorstGrowthRateChange: (value: number) => void;
  isLoading: boolean;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ClientForecastTab({
  clientId,
  financials,
  baseForecast,
  bestForecast,
  worstForecast,
  baseGrowthRate,
  bestGrowthRate,
  worstGrowthRate,
  onBaseGrowthRateChange,
  onBestGrowthRateChange,
  onWorstGrowthRateChange,
  isLoading,
}: ClientForecastTabProps) {
  const [forecastModel, setForecastModel] = useState<ForecastModel>("deterministic");
  const [draftBaseGrowthRate, setDraftBaseGrowthRate] = useState(baseGrowthRate);
  const [draftBestGrowthRate, setDraftBestGrowthRate] = useState(bestGrowthRate);
  const [draftWorstGrowthRate, setDraftWorstGrowthRate] = useState(worstGrowthRate);
  const [prophetForecast, setProphetForecast] = useState<ProphetForecastResponse | null>(null);
  const [isLoadingProphet, setIsLoadingProphet] = useState(false);
  const [prophetError, setProphetError] = useState<string | null>(null);

  useEffect(() => {
    setDraftBaseGrowthRate(baseGrowthRate);
  }, [baseGrowthRate]);

  useEffect(() => {
    setDraftBestGrowthRate(bestGrowthRate);
  }, [bestGrowthRate]);

  useEffect(() => {
    setDraftWorstGrowthRate(worstGrowthRate);
  }, [worstGrowthRate]);

  useEffect(() => {
    if (forecastModel !== "prophet") {
      return;
    }

    let cancelled = false;

    async function loadProphetForecast() {
      setIsLoadingProphet(true);
      setProphetError(null);
      try {
        const response = await getClientForecast(clientId, 0, "prophet");
        if (!cancelled) {
          setProphetForecast(response as ProphetForecastResponse);
        }
      } catch (err) {
        if (!cancelled) {
          setProphetError(
            err instanceof Error ? err.message : "Failed to load Prophet forecast",
          );
          setProphetForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingProphet(false);
        }
      }
    }

    loadProphetForecast();
    return () => {
      cancelled = true;
    };
  }, [clientId, forecastModel]);

  if (isLoading && forecastModel === "deterministic") {
    return null;
  }

  return (
    <>
      <section>
        <h3 className="deal-result-panel__breaches-title">Forecast Model</h3>

        <label className="deal-form__field">
          <span className="deal-form__label">Model</span>
          <select
            className="deal-form__input"
            value={forecastModel}
            onChange={(e) => setForecastModel(e.target.value as ForecastModel)}
          >
            <option value="deterministic">Deterministic Forecast</option>
            <option value="prophet">Prophet Forecast</option>
          </select>
        </label>

        <p className="clients-panel__meta">
          {forecastModel === "deterministic"
            ? "Uses user-defined assumptions such as revenue growth rate."
            : "Uses historical data patterns to estimate future revenue."}
        </p>
      </section>

      {forecastModel === "deterministic" ? (
        <>
          <section>
            <h3 className="deal-result-panel__breaches-title">
              Revenue & Gross Profit Forecast
            </h3>

            <label className="deal-form__field">
              <span className="deal-form__label">Revenue Growth Rate (%)</span>

              <input
                className="deal-form__input"
                type="number"
                value={draftBaseGrowthRate * 100}
                onChange={(e) =>
                  setDraftBaseGrowthRate(Number(e.target.value) / 100)
                }
              />
            </label>

            <button
              className="deal-form__submit"
              type="button"
              onClick={() => onBaseGrowthRateChange(draftBaseGrowthRate)}
            >
              Update
            </button>

            <RevenueGrossProfitChart
              financials={financials}
              baseForecast={baseForecast}
            />
          </section>

          <section>
            <h3 className="deal-result-panel__breaches-title">
              Best / Worst Case Scenarios
            </h3>

            {[
              {
                label: "Base Case Growth Rate (%)",
                value: draftBaseGrowthRate,
                setValue: setDraftBaseGrowthRate,
                update: onBaseGrowthRateChange,
              },
              {
                label: "Best Case Growth Rate (%)",
                value: draftBestGrowthRate,
                setValue: setDraftBestGrowthRate,
                update: onBestGrowthRateChange,
              },
              {
                label: "Worst Case Growth Rate (%)",
                value: draftWorstGrowthRate,
                setValue: setDraftWorstGrowthRate,
                update: onWorstGrowthRateChange,
              },
            ].map((item) => (
              <div key={item.label}>
                <label className="deal-form__field">
                  <span className="deal-form__label">{item.label}</span>

                  <input
                    className="deal-form__input"
                    type="number"
                    value={item.value * 100}
                    onChange={(e) => item.setValue(Number(e.target.value) / 100)}
                  />
                </label>

                <button
                  className="deal-form__submit"
                  type="button"
                  onClick={() => item.update(item.value)}
                >
                  Update
                </button>
              </div>
            ))}

            <RevenueScenarioChart
              financials={financials}
              baseForecast={baseForecast}
              bestForecast={bestForecast}
              worstForecast={worstForecast}
            />
          </section>
        </>
      ) : (
        <section>
          <h3 className="deal-result-panel__breaches-title">Prophet Forecast</h3>

          {prophetError ? <p className="dashboard-error">{prophetError}</p> : null}
          {isLoadingProphet ? (
            <p className="clients-panel__hint">Loading Prophet forecast…</p>
          ) : null}

          {!isLoadingProphet && prophetForecast ? (
            <>
              <ProphetForecastChart
                historical={
                  financials?.historical.map((record) => ({
                    month: record.month,
                    revenue: record.revenue,
                  })) ?? []
                }
                forecast={prophetForecast.forecast ?? []}
              />
              {(prophetForecast.forecast ?? []).length > 0 ? (
                <div className="dashboard-table-wrap">
                  <table className="dashboard-table">
                    <thead>
                      <tr>
                        <th>Month</th>
                        <th>Revenue</th>
                        <th>Lower Bound</th>
                        <th>Upper Bound</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(prophetForecast.forecast ?? []).map((row) => (
                        <tr key={row.month}>
                          <td>{row.month.slice(0, 7)}</td>
                          <td className="dashboard-table__num">
                            {formatCurrency(row.revenue)}
                          </td>
                          <td className="dashboard-table__num">
                            {formatCurrency(row.lower_bound)}
                          </td>
                          <td className="dashboard-table__num">
                            {formatCurrency(row.upper_bound)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </>
          ) : null}
        </section>
      )}
    </>
  );
}
