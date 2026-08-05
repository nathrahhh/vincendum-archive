export { request } from "./client";
export { fetchPortfolio } from "./portfolio";
export { fetchDeals, postApproveDeal, postEvaluateDeal, postRejectDeal } from "./deals";
export { fetchBreaches } from "./risk";
export {
  fetchClients,
  fetchClient,
  fetchClientFinancials,
  fetchClientForecast,
  postClientFinancial,
  updateClientCreditLimit,
} from "./clients";
export { postClientApplication } from "./clientApplications";
export { fetchHealth } from "./health";
export { postFinancialStatementExtract } from "./parsing";
export { fetchCurrentUser } from "./users";
export { postLenderOnboard } from "./lenders";
