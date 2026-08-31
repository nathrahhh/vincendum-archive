import { useCallback, useEffect, useState } from "react";
import { approveDeal, getDeals, rejectDeal } from "../services/dealService";
import type { DealApprovalPayload, DealRecord } from "../types";

const statusClass: Record<string, string> = {
  PENDING: "dashboard-badge dashboard-badge--warning",
  APPROVED: "dashboard-badge dashboard-badge--approved",
  REJECTED: "dashboard-badge dashboard-badge--rejected",
};

function formatValue(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function buildInitialApprovalPayload(deal: DealRecord): DealApprovalPayload {
  const startDate = new Date();
  const firstPaymentDate = new Date(
    startDate.getFullYear(),
    startDate.getMonth() + 1,
    1,
  );

  return {
    principal_amount: deal.value,
    interest_rate: 7,
    interest_rate_type: "fixed",
    repayment_method: "amortizing",
    term_months: deal.term_months ?? 12,
    start_date: toDateInputValue(startDate),
    payment_frequency: "monthly",
    first_payment_date: toDateInputValue(firstPaymentDate),
    maturity_date: null,
  };
}

export default function EvaluationsPage() {
  const [deals, setDeals] = useState<DealRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [approvalDeal, setApprovalDeal] = useState<DealRecord | null>(null);
  const [approvalPayload, setApprovalPayload] =
    useState<DealApprovalPayload | null>(null);

  const loadDeals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDeals();
      setDeals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deals");
      setDeals([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  function openApproval(deal: DealRecord) {
    setApprovalDeal(deal);
    setApprovalPayload(buildInitialApprovalPayload(deal));
    setError(null);
  }

  function closeApproval() {
    setApprovalDeal(null);
    setApprovalPayload(null);
  }

  function updateApprovalField<K extends keyof DealApprovalPayload>(
    field: K,
    value: DealApprovalPayload[K],
  ) {
    setApprovalPayload((current) =>
      current ? { ...current, [field]: value } : current,
    );
  }

  async function handleApproveSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!approvalDeal || !approvalPayload) {
      return;
    }

    setActionLoadingId(approvalDeal.id);
    setError(null);
    try {
      await approveDeal(approvalDeal.id, approvalPayload);
      closeApproval();
      await loadDeals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve deal");
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleReject(id: number) {
    setActionLoadingId(id);
    setError(null);
    try {
      await rejectDeal(id);
      if (approvalDeal?.id === id) {
        closeApproval();
      }
      await loadDeals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject deal");
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div className="evaluations-page">
      <section className="dashboard-panel">
        {error ? <p className="dashboard-error">{error}</p> : null}
        {isLoading ? <p className="dashboard-panel__subtitle">Loading evaluations…</p> : null}
        {!isLoading && !error && deals.length === 0 ? (
          <p className="dashboard-panel__subtitle">No evaluated deals yet.</p>
        ) : null}
        {!isLoading && deals.length > 0 ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Value</th>
                  <th>Term (months)</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.name}</td>
                    <td className="dashboard-table__num">{formatValue(deal.value)}</td>
                    <td className="dashboard-table__num">
                      {deal.term_months ?? "—"}
                    </td>
                    <td>
                      <span className={statusClass[deal.status ?? ""] ?? "dashboard-badge"}>
                        {deal.status ?? "—"}
                      </span>
                    </td>
                    <td>
                      {deal.status === "PENDING" ? (
                        <>
                          <button
                            type="button"
                            disabled={actionLoadingId === deal.id}
                            onClick={() => openApproval(deal)}
                          >
                            Approve
                          </button>{" "}
                          <button
                            type="button"
                            disabled={actionLoadingId === deal.id}
                            onClick={() => handleReject(deal.id)}
                          >
                            Reject
                          </button>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {approvalDeal && approvalPayload ? (
          <form className="deal-form" onSubmit={handleApproveSubmit}>
            <h3 className="deal-form__title">
              Approve Deal: {approvalDeal.name}
            </h3>
            <p className="deal-form__subtitle">
              Set lender-confirmed repayment terms before approval.
            </p>

            <fieldset
              className="deal-form__section"
              disabled={actionLoadingId === approvalDeal.id}
            >
              <label className="deal-form__field">
                <span className="deal-form__label">Principal Amount (USD)</span>
                <input
                  className="deal-form__input"
                  type="number"
                  min="0"
                  step="any"
                  value={approvalPayload.principal_amount}
                  onChange={(e) =>
                    updateApprovalField("principal_amount", Number(e.target.value))
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Interest Rate (%)</span>
                <input
                  className="deal-form__input"
                  type="number"
                  min="0"
                  step="any"
                  value={approvalPayload.interest_rate}
                  onChange={(e) =>
                    updateApprovalField("interest_rate", Number(e.target.value))
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Interest Rate Type</span>
                <input
                  className="deal-form__input"
                  type="text"
                  value={approvalPayload.interest_rate_type}
                  onChange={(e) =>
                    updateApprovalField("interest_rate_type", e.target.value)
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Repayment Method</span>
                <input
                  className="deal-form__input"
                  type="text"
                  value={approvalPayload.repayment_method}
                  onChange={(e) =>
                    updateApprovalField("repayment_method", e.target.value)
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Term (months)</span>
                <input
                  className="deal-form__input"
                  type="number"
                  min="1"
                  step="1"
                  value={approvalPayload.term_months}
                  onChange={(e) =>
                    updateApprovalField("term_months", Number(e.target.value))
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Start Date</span>
                <input
                  className="deal-form__input"
                  type="date"
                  value={approvalPayload.start_date}
                  onChange={(e) =>
                    updateApprovalField("start_date", e.target.value)
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Payment Frequency</span>
                <input
                  className="deal-form__input"
                  type="text"
                  value={approvalPayload.payment_frequency}
                  onChange={(e) =>
                    updateApprovalField("payment_frequency", e.target.value)
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">First Payment Date</span>
                <input
                  className="deal-form__input"
                  type="date"
                  value={approvalPayload.first_payment_date}
                  onChange={(e) =>
                    updateApprovalField("first_payment_date", e.target.value)
                  }
                  required
                />
              </label>

              <label className="deal-form__field">
                <span className="deal-form__label">Maturity Date</span>
                <input
                  className="deal-form__input"
                  type="date"
                  value={approvalPayload.maturity_date ?? ""}
                  onChange={(e) =>
                    updateApprovalField(
                      "maturity_date",
                      e.target.value === "" ? null : e.target.value,
                    )
                  }
                />
              </label>
            </fieldset>

            <button
              className="deal-form__submit"
              type="submit"
              disabled={actionLoadingId === approvalDeal.id}
            >
              {actionLoadingId === approvalDeal.id
                ? "Approving..."
                : "Confirm Approval"}
            </button>{" "}
            <button
              type="button"
              disabled={actionLoadingId === approvalDeal.id}
              onClick={closeApproval}
            >
              Cancel
            </button>
          </form>
        ) : null}
      </section>
    </div>
  );
}
