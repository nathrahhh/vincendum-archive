import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  defaultPathForRole,
  useCurrentUser,
} from "../auth/CurrentUserProvider";
import { onboardLender } from "../services/lenderService";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, isLoading, refreshUser } = useCurrentUser();
  const [name, setName] = useState("");
  const [capitalBase, setCapitalBase] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !user) {
      return;
    }

    if (user.role === "client") {
      navigate("/client", { replace: true });
      return;
    }

    if (user.lender_id !== null) {
      navigate(defaultPathForRole("admin"), { replace: true });
    }
  }, [isLoading, user, navigate]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Lender name is required");
      return;
    }

    const capitalValue = Number(capitalBase);
    if (!Number.isFinite(capitalValue) || capitalValue <= 0) {
      setError("Total lending capital must be greater than zero");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onboardLender({ name: trimmed, capital_base: capitalValue });
      await refreshUser();
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create lender");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return <div>Loading account...</div>;
  }

  return (
    <div className="deal-form">
      <h1 className="deal-form__title">Welcome</h1>
      <p className="deal-form__subtitle">
        Create your lending organisation to finish setup. This only needs to be
        done once.
      </p>

      {error ? <p className="dashboard-error">{error}</p> : null}

      <form onSubmit={handleSubmit}>
        <label className="deal-form__field">
          <span className="deal-form__label">Lender name</span>
          <span className="deal-form__hint">
            Enter your lender or organisation name.
          </span>
          <input
            className="deal-form__input"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. ABC Capital"
            required
            disabled={isSubmitting}
          />
        </label>

        <label className="deal-form__field">
          <span className="deal-form__label">Total lending capital</span>
          <span className="deal-form__hint">
            How much capital does your organisation have available for lending?
          </span>
          <input
            className="deal-form__input"
            type="number"
            min={1}
            step="any"
            value={capitalBase}
            onChange={(event) => setCapitalBase(event.target.value)}
            placeholder="e.g. 10000000"
            required
            disabled={isSubmitting}
          />
        </label>

        <button className="deal-form__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create Lender"}
        </button>
      </form>
    </div>
  );
}
