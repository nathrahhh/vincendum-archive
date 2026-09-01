export { request } from "./client";
export {
  createPortfolio,
  fetchPortfolio,
  fetchPortfolios,
  updatePortfolio,
} from "./portfolio";
export { fetchDeals, fetchClientDeals, postApproveDeal, postMyClientDeal, postRejectDeal } from "./deals";
export { fetchBreaches, postResolveBreach } from "./risk";
export {
  fetchClients,
  fetchClient,
  fetchClientFinancials,
  fetchClientForecast,
  fetchClientForecastBacktest,
  fetchMyClient,
  fetchMyClientDeals,
  fetchMyClientFinancials,
  fetchMyClientForecast,
  fetchMyClientForecastBacktest,
  postClientFinancial,
  postClientInvite,
  updateClientCreditLimit,
} from "./clients";
export { postClientApplication } from "./clientApplications";
export { fetchHealth } from "./health";
export { postFinancialStatementExtract } from "./parsing";
export { fetchCurrentUser } from "./users";
export {
  fetchOpenBankingAccounts,
  fetchOpenBankingTransactions,
  postOpenBankingConnect,
} from "./openBanking";
