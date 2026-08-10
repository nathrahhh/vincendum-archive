import { useEffect, useState } from "react";
import type { Client } from "../../types";
import {
  inviteClientUser,
  updateClientCreditLimit,
} from "../../services/clientService";

type ClientOverviewTabProps = {
  client: Client;
  onClientUpdated: () => Promise<void> | void;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function ClientOverviewTab({
  client,
  onClientUpdated,
}: ClientOverviewTabProps) {
  const [draftCreditLimit, setDraftCreditLimit] = useState(
    client.credit_limit ?? 0,
  );
  const [isUpdatingCreditLimit, setIsUpdatingCreditLimit] = useState(false);
  const [creditLimitError, setCreditLimitError] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [invitationUrl, setInvitationUrl] = useState<string | null>(null);

  useEffect(() => {
    setDraftCreditLimit(client.credit_limit ?? 0);
    setCreditLimitError(null);
    setInviteEmail("");
    setInviteError(null);
    setInvitationUrl(null);
  }, [client.id, client.credit_limit]);

  async function handleUpdateCreditLimit() {
    setIsUpdatingCreditLimit(true);
    setCreditLimitError(null);

    try {
      await updateClientCreditLimit(client.id, Number(draftCreditLimit));
      await onClientUpdated();
    } catch (err) {
      setCreditLimitError(
        err instanceof Error ? err.message : "Failed to update credit limit",
      );
    } finally {
      setIsUpdatingCreditLimit(false);
    }
  }

  async function handleInviteClientUser() {
    const email = inviteEmail.trim();
    if (!email) {
      return;
    }

    setIsInviting(true);
    setInviteError(null);
    setInvitationUrl(null);

    try {
      const invitation = await inviteClientUser(client.id, email);
      setInviteEmail("");
      setInvitationUrl(invitation.invitation_url);
    } catch (err) {
      setInviteError(
        err instanceof Error ? err.message : "Failed to invite client user",
      );
    } finally {
      setIsInviting(false);
    }
  }

  return (
    <>
      <section>
        <h3 className="deal-result-panel__breaches-title">Credit Limit</h3>

        <label className="deal-form__field">
          <span className="deal-form__label">Credit Limit (USD)</span>

          <input
            className="deal-form__input"
            type="number"
            min="0"
            step="any"
            value={draftCreditLimit}
            onChange={(e) => setDraftCreditLimit(Number(e.target.value))}
          />
        </label>

        <button
          className="deal-form__submit"
          type="button"
          disabled={isUpdatingCreditLimit}
          onClick={handleUpdateCreditLimit}
        >
          {isUpdatingCreditLimit ? "Updating…" : "Update"}
        </button>

        {creditLimitError && (
          <p className="dashboard-error">{creditLimitError}</p>
        )}
      </section>

      <section>
        <h3 className="deal-result-panel__breaches-title">Exposure</h3>

        <p className="clients-panel__meta">
          Current exposure: {formatCurrency(client.current_exposure ?? 0)}
        </p>

        <p className="clients-panel__meta">
          Remaining credit: {formatCurrency(client.remaining_credit ?? 0)}
        </p>

        <p className="clients-panel__meta">
          Utilization: {formatPercent(client.utilization_pct ?? 0)}
        </p>
      </section>

      <section>
        <h3 className="deal-result-panel__breaches-title">Invite client user</h3>

        <label className="deal-form__field">
          <span className="deal-form__label">Email</span>

          <input
            className="deal-form__input"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="client@example.com"
            disabled={isInviting}
          />
        </label>

        <button
          className="deal-form__submit"
          type="button"
          disabled={isInviting || !inviteEmail.trim()}
          onClick={handleInviteClientUser}
        >
          {isInviting ? "Inviting…" : "Invite user"}
        </button>

        {inviteError && <p className="dashboard-error">{inviteError}</p>}

        {invitationUrl && (
          <p className="clients-panel__meta">
            Invitation URL:{" "}
            <a href={invitationUrl} target="_blank" rel="noreferrer">
              {invitationUrl}
            </a>
          </p>
        )}
      </section>
    </>
  );
}
