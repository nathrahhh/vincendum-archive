import { useState } from "react";
import { DealForm, DealResultPanel } from "../components/deals";
import { evaluateDeal } from "../services/dealService";
import type { DealPayload, RiskEvaluation } from "../types";

export default function DealPage() {
  const [result, setResult] = useState<RiskEvaluation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleEvaluate(deal: DealPayload) {
    setIsLoading(true);
    setError(null);
    try {
      const evaluation = await evaluateDeal(deal);
      setResult(evaluation);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Failed to evaluate deal");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="deal-page">
      <div className="deal-page__form">
        <DealForm onSubmit={handleEvaluate} isLoading={isLoading} />
      </div>
      <DealResultPanel result={result} error={error} isLoading={isLoading} />
    </div>
  );
}
