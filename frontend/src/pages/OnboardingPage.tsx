import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, onboardLender } from "../services/authService";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function checkOnboardingStatus() {
      try {
        const user = await getCurrentUser();
        if (!cancelled && user.lender_id !== null) {
          navigate("/dashboard", { replace: true });
        }
      } catch {
        // Stay on onboarding; submit will surface auth/API errors.
      }
    }

    checkOnboardingStatus();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Lender name is required");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onboardLender({ name: trimmed });
      await getCurrentUser();
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create lender");
    } finally {
      setIsSubmitting(false);
    }
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

        <button className="deal-form__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create Lender"}
        </button>
      </form>
    </div>
  );
}
