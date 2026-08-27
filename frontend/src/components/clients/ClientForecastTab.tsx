import { useEffect, useState } from "react";
import type {
  ClientFinancials,
  ClientForecast,
  ForecastBacktestResponse,
  ForecastModel,
  ProphetForecastResponse,
} from "../../types/clients";
import {
  getClientForecast,
  getClientForecastBacktest,
  getMyClientForecast,
  getMyClientForecastBacktest,
} from "../../services/clientService";
import ForecastBacktestChart, {
  formatForecastModelName,
} from "./ForecastBacktestChart";
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
  /** admin: /clients/{id}/forecast; me: /client/me/forecast */
  forecastApi?: "admin" | "me";
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMae(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatUnavailableReason(reason: string | null): string {
  switch (reason) {
    case "insufficient_history":
      return "Insufficient history";
    case "non_consecutive_months":
      return "Non-consecutive months";
    case "model_fit_failed":
      return "Model fit failed";
    default:
      return reason ?? "Unavailable";
  }
}

function buildRecommendationExplanation(
  backtest: ForecastBacktestResponse,
): string {
  const bestModel = backtest.best_model;
  if (!bestModel) {
    return "";
  }

  const bestResult = backtest.results.find(
    (result) => result.model === bestModel && result.available,
  );
  const displayName = formatForecastModelName(bestModel);
  const maeText =
    bestResult?.mae != null ? formatMae(bestResult.mae) : "an unavailable MAE";

  return `Based on the most recent ${backtest.holdout_months} months of historical holdout testing, ${displayName} produced the lowest mean absolute error (MAE) of ${maeText}, so it performed best among the tested models on this client's historical data. This reflects past holdout performance only and is not a guarantee of future accuracy.`;
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
  forecastApi = "admin",
}: ClientForecastTabProps) {
  const [forecastModel, setForecastModel] = useState<ForecastModel>("deterministic");
  const [draftBaseGrowthRate, setDraftBaseGrowthRate] = useState(baseGrowthRate);
  const [draftBestGrowthRate, setDraftBestGrowthRate] = useState(bestGrowthRate);
  const [draftWorstGrowthRate, setDraftWorstGrowthRate] = useState(worstGrowthRate);
  const [forecastBacktest, setForecastBacktest] =
    useState<ForecastBacktestResponse | null>(null);
  const [isLoadingBacktest, setIsLoadingBacktest] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
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
    let cancelled = false;

    async function loadForecastBacktest() {
      setIsLoadingBacktest(true);
      setBacktestError(null);
      try {
        const response =
          forecastApi === "me"
            ? await getMyClientForecastBacktest()
            : await getClientForecastBacktest(clientId);
        if (!cancelled) {
          setForecastBacktest(response);
        }
      } catch (err) {
        if (!cancelled) {
          setBacktestError(
            err instanceof Error ? err.message : "Failed to load forecast backtest",
          );
          setForecastBacktest(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingBacktest(false);
        }
      }
    }

    loadForecastBacktest();
    return () => {
      cancelled = true;
    };
  }, [clientId, forecastApi]);

  useEffect(() => {
    if (forecastModel !== "prophet") {
      return;
    }

    let cancelled = false;

    async function loadProphetForecast() {
      setIsLoadingProphet(true);
      setProphetError(null);
      try {
        const response =
          forecastApi === "me"
            ? await getMyClientForecast(0, "prophet")
            : await getClientForecast(clientId, 0, "prophet");
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
  }, [clientId, forecastModel, forecastApi]);

  const availableResults =
    forecastBacktest?.results.filter((result) => result.available) ?? [];
  const allModelsUnavailable =
    forecastBacktest != null &&
    forecastBacktest.results.length > 0 &&
    availableResults.length === 0;
  const bestResult = forecastBacktest?.best_model
    ? forecastBacktest.results.find(
        (result) =>
          result.model === forecastBacktest.best_model && result.available,
      )
    : null;

  if (isLoading && forecastModel === "deterministic") {
    return null;
  }

  return (
    <>
      <section>
        <h3 className="deal-result-panel__breaches-title">Model Recommendation</h3>

        {backtestError ? <p className="dashboard-error">{backtestError}</p> : null}
        {isLoadingBacktest ? (
          <p className="clients-panel__hint">Evaluating forecasting models…</p>
        ) : null}

        {!isLoadingBacktest && !backtestError && forecastBacktest ? (
          <>
            {forecastBacktest.best_model && bestResult ? (
              <>
                <p className="clients-panel__meta">
                  <strong>Recommended model:</strong>{" "}
                  {formatForecastModelName(forecastBacktest.best_model)}
                </p>
                <p className="clients-panel__meta">
                  <strong>Historical MAE:</strong>{" "}
                  {bestResult.mae != null ? formatMae(bestResult.mae) : "—"}
                </p>
                <p className="clients-panel__meta">
                  {buildRecommendationExplanation(forecastBacktest)}
                </p>
              </>
            ) : (
              <p className="clients-panel__meta">
                No model recommendation is available for this client.
                {allModelsUnavailable
                  ? " The historical data may be insufficient or non-consecutive for backtesting."
                  : null}
              </p>
            )}

            {!allModelsUnavailable ? (
              <>
                <ForecastBacktestChart
                  results={forecastBacktest.results}
                  bestModel={forecastBacktest.best_model}
                />

                <div className="dashboard-table-wrap">
                  <table className="dashboard-table">
                    <thead>
                      <tr>
                        <th>Model</th>
                        <th>MAE</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecastBacktest.results.map((result) => {
                        const isRecommended =
                          result.available &&
                          result.model === forecastBacktest.best_model;
                        const status = isRecommended
                          ? "Recommended"
                          : result.available
                            ? "Tested"
                            : formatUnavailableReason(result.unavailable_reason);

                        return (
                          <tr
                            key={result.model}
                            style={
                              isRecommended
                                ? { backgroundColor: "rgba(5, 150, 105, 0.08)" }
                                : undefined
                            }
                          >
                            <td>{formatForecastModelName(result.model)}</td>
                            <td className="dashboard-table__num">
                              {result.available && result.mae != null
                                ? formatMae(result.mae)
                                : "—"}
                            </td>
                            <td>{status}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}
          </>
        ) : null}
      </section>

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
