export default function PortfolioPlaceholder() {
  return (
    <>
      <p>Portfolio monitoring is available on the dashboard.</p>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Use <code>fetchPortfolios()</code> and <code>fetchPortfolio()</code> in{" "}
        <code>src/services/portfolioService.ts</code>.
      </p>
    </>
  );
}
