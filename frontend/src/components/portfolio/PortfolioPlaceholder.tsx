export default function PortfolioPlaceholder() {
  return (
    <>
      <p>Placeholder for portfolio positions loaded from the backend API.</p>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Wire up <code>getPortfolio()</code> in <code>src/services/portfolioService.ts</code> when
        ready.
      </p>
    </>
  );
}
