import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ExposureChart, PortfolioSummaryPanel } from "../components/dashboard";
import { fetchIndustryExposure } from "../services/lenderService";
import {
  createPortfolio,
  fetchPortfolio,
  fetchPortfolios,
  updatePortfolio,
} from "../services/portfolioService";
import type {
  IndustryExposure,
  PortfolioSummary,
  PortfolioUpdateRequest,
} from "../types";

export default function DashboardPage() {
  const [summaries, setSummaries] = useState<PortfolioSummary[]>([]);
  const [industryExposure, setIndustryExposure] = useState<IndustryExposure[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [industryExposureLoading, setIndustryExposureLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createAllocation, setCreateAllocation] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSubmitting, setCreateSubmitting] = useState(false);

  const loadPortfolioSummaries = useCallback(async () => {
    const records = await fetchPortfolios();
    if (records.length === 0) {
      setSummaries([]);
      return;
    }

    const portfolioSummaries = await Promise.all(
      records.map((portfolio) => fetchPortfolio(portfolio.id)),
    );
    setSummaries(
      portfolioSummaries.sort((left, right) => left.portfolio_id - right.portfolio_id),
    );
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);
      try {
        await loadPortfolioSummaries();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load portfolios");
          setSummaries([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [loadPortfolioSummaries]);

  useEffect(() => {
    let cancelled = false;

    async function loadIndustryExposure() {
      setIndustryExposureLoading(true);
      try {
        const data = await fetchIndustryExposure();
        if (!cancelled) {
          setIndustryExposure(data);
        }
      } catch (err) {
        console.error("Failed to load industry exposure", err);
        if (!cancelled) {
          setIndustryExposure([]);
        }
      } finally {
        if (!cancelled) {
          setIndustryExposureLoading(false);
        }
      }
    }

    void loadIndustryExposure();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleUpdatePortfolio = useCallback(
    async (portfolioId: number, payload: PortfolioUpdateRequest) => {
      await updatePortfolio(portfolioId, payload);
      const updatedSummary = await fetchPortfolio(portfolioId);
      setSummaries((current) =>
        current
          .map((summary) =>
            summary.portfolio_id === portfolioId ? updatedSummary : summary,
          )
          .sort((left, right) => left.portfolio_id - right.portfolio_id),
      );
    },
    [],
  );

  function openCreateForm() {
    setCreateError(null);
    setCreateName("");
    setCreateAllocation("");
    setShowCreateForm(true);
  }

  function closeCreateForm() {
    setCreateError(null);
    setCreateName("");
    setCreateAllocation("");
    setShowCreateForm(false);
  }

  async function handleCreatePortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateError(null);
    setCreateSubmitting(true);
    try {
      const created = await createPortfolio({
        name: createName.trim(),
        capital_allocation: Number(createAllocation),
      });
      const summary = await fetchPortfolio(created.id);
      setSummaries((current) =>
        [...current, summary].sort((left, right) => left.portfolio_id - right.portfolio_id),
      );
      closeCreateForm();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create portfolio");
    } finally {
      setCreateSubmitting(false);
    }
  }

  return (
    <div className="dashboard">
      {error ? <p className="dashboard-error">{error}</p> : null}

      {!isLoading ? (
        <div className="dashboard-toolbar">
          <button
            type="button"
            className="dashboard-button"
            onClick={openCreateForm}
          >
            Add Portfolio
          </button>
        </div>
      ) : null}

      {showCreateForm ? (
        <section className="dashboard-panel">
          <h2 className="dashboard-panel__title">Add Portfolio</h2>
          <form className="dashboard-form" onSubmit={handleCreatePortfolio}>
            <label>
              Portfolio name
              <input
                type="text"
                value={createName}
                onChange={(event) => setCreateName(event.target.value)}
                required
              />
            </label>
            <label>
              Capital allocation
              <input
                type="number"
                min="0"
                step="any"
                value={createAllocation}
                onChange={(event) => setCreateAllocation(event.target.value)}
                required
              />
            </label>
            {createError ? <p className="dashboard-error">{createError}</p> : null}
            <div className="dashboard-form__actions">
              <button type="submit" disabled={createSubmitting}>
                {createSubmitting ? "Creating…" : "Create"}
              </button>
              <button
                type="button"
                className="dashboard-button dashboard-button--secondary"
                onClick={closeCreateForm}
                disabled={createSubmitting}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      ) : null}

      {isLoading ? (
        <p className="dashboard-panel__subtitle">Loading portfolios…</p>
      ) : null}

      {!isLoading && summaries.length > 0 ? (
        <section className="dashboard-portfolio-cards">
          {summaries.map((summary) => (
            <PortfolioSummaryPanel
              key={summary.portfolio_id}
              summary={summary}
              onUpdate={handleUpdatePortfolio}
            />
          ))}
        </section>
      ) : null}

      {!isLoading && summaries.length === 0 ? (
        <section className="dashboard-panel">
          <h2 className="dashboard-panel__title">Portfolios</h2>
          <p className="dashboard-panel__subtitle">
            No portfolios yet. Use Add Portfolio to create one.
          </p>
        </section>
      ) : null}

      <ExposureChart
        exposure={industryExposure}
        isLoading={industryExposureLoading}
      />
    </div>
  );
}
