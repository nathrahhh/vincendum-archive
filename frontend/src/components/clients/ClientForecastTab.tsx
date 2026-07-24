import { useEffect, useState } from "react";
import type { ClientFinancials, ClientForecast } from "../../types";
import RevenueGrossProfitChart from "./RevenueGrossProfitChart";
import RevenueScenarioChart from "./RevenueScenarioChart";

type ClientForecastTabProps = {
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

export default function ClientForecastTab({
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
  const [draftBaseGrowthRate, setDraftBaseGrowthRate] = useState(baseGrowthRate);
  const [draftBestGrowthRate, setDraftBestGrowthRate] = useState(bestGrowthRate);
  const [draftWorstGrowthRate, setDraftWorstGrowthRate] = useState(worstGrowthRate);

  useEffect(() => {
    setDraftBaseGrowthRate(baseGrowthRate);
  }, [baseGrowthRate]);

  useEffect(() => {
    setDraftBestGrowthRate(bestGrowthRate);
  }, [bestGrowthRate]);

  useEffect(() => {
    setDraftWorstGrowthRate(worstGrowthRate);
  }, [worstGrowthRate]);

  if (isLoading) {
    return null;
  }

  return (
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
  );
}
