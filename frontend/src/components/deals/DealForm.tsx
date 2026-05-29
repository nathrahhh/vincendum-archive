import { useState } from "react";
import type { FormEvent } from "react";
import type { DealPayload } from "../../types";

type DealFormProps = {
  onSubmit: (deal: DealPayload) => void;
  isLoading?: boolean;
};

export default function DealForm({ onSubmit, isLoading = false }: DealFormProps) {
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [industry, setIndustry] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit({
      name: name.trim(),
      value: Number(value),
      industry: industry.trim(),
    });
  }

  return (
    <form className="deal-form" onSubmit={handleSubmit}>
      <h2 className="deal-form__title">New Deal</h2>
      <p className="deal-form__subtitle">Enter deal details for evaluation</p>

      <label className="deal-form__field">
        <span className="deal-form__label">Name</span>
        <input
          className="deal-form__input"
          type="text"
          name="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Zeta Healthcare Bridge"
          required
          disabled={isLoading}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">Value</span>
        <input
          className="deal-form__input"
          type="number"
          name="value"
          min="0"
          step="any"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="e.g. 1500000"
          required
          disabled={isLoading}
        />
      </label>

      <label className="deal-form__field">
        <span className="deal-form__label">Industry</span>
        <input
          className="deal-form__input"
          type="text"
          name="industry"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          placeholder="e.g. Healthcare"
          required
          disabled={isLoading}
        />
      </label>

      <button className="deal-form__submit" type="submit" disabled={isLoading}>
        {isLoading ? "Evaluating…" : "Evaluate"}
      </button>
    </form>
  );
}
