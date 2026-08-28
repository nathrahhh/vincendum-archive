import { useEffect, useState } from "react";
import type {
  ForecastBacktestResponse,
  StatisticalForecastResponse,
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
import RecommendedForecastChart from "./RecommendedForecastChart";

type ClientForecastTabProps = {
  clientId: number;
  /** admin: /clients/{id}/forecast; me: /client/me/forecast */
  forecastApi?: "admin" | "me";
};

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
  forecastApi = "admin",
}: ClientForecastTabProps) {
  const [forecastBacktest, setForecastBacktest] =
    useState<ForecastBacktestResponse | null>(null);
  const [isLoadingBacktest, setIsLoadingBacktest] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);

  const [selectedForecast, setSelectedForecast] =
    useState<StatisticalForecastResponse | null>(null);
  const [isLoadingForecast, setIsLoadingForecast] = useState(false);
  const [forecastError, setForecastError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadForecastBacktest() {
      setIsLoadingBacktest(true);
      setBacktestError(null);
      setSelectedForecast(null);
      setForecastError(null);
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
            err instanceof Error
              ? err.message
              : "Failed to load forecast backtest",
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
    const bestModel = forecastBacktest?.best_model ?? null;
    if (!bestModel) {
      setSelectedForecast(null);
      setForecastError(null);
      setIsLoadingForecast(false);
      return;
    }

    let cancelled = false;
    const model = bestModel;

    async function loadRecommendedForecast() {
      setIsLoadingForecast(true);
      setForecastError(null);
      try {
        const response =
          forecastApi === "me"
            ? await getMyClientForecast(model)
            : await getClientForecast(clientId, model);

        if (!cancelled) {
          if (response.unavailable_reason || response.forecast.length === 0) {
            setSelectedForecast(response);
            setForecastError(
              response.unavailable_reason
                ? `Forecast unavailable: ${formatUnavailableReason(response.unavailable_reason)}`
                : `No forecast points returned for ${formatForecastModelName(model)}.`,
            );
            return;
          }
          setSelectedForecast(response);
        }
      } catch (err) {
        if (!cancelled) {
          setForecastError(
            err instanceof Error
              ? err.message
              : `Failed to load ${formatForecastModelName(model)} forecast`,
          );
          setSelectedForecast(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingForecast(false);
        }
      }
    }

    loadRecommendedForecast();
    return () => {
      cancelled = true;
    };
  }, [clientId, forecastApi, forecastBacktest?.best_model]);

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
  const recommendedModelName = forecastBacktest?.best_model
    ? formatForecastModelName(forecastBacktest.best_model)
    : null;

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
                  <strong>Recommended model:</strong> {recommendedModelName}
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

      {forecastBacktest?.best_model ? (
        <section>
          <h3 className="deal-result-panel__breaches-title">Recommended Forecast</h3>
          <p className="clients-panel__meta">
            <strong>Selected model:</strong>{" "}
            {formatForecastModelName(forecastBacktest.best_model)}
          </p>

          {forecastError ? <p className="dashboard-error">{forecastError}</p> : null}
          {isLoadingForecast ? (
            <p className="clients-panel__hint">
              Loading {formatForecastModelName(forecastBacktest.best_model)}{" "}
              forecast…
            </p>
          ) : null}

          {!isLoadingForecast && selectedForecast ? (
            <RecommendedForecastChart
              historical={selectedForecast.historical}
              forecast={selectedForecast.forecast}
            />
          ) : null}
        </section>
      ) : null}
    </>
  );
}
