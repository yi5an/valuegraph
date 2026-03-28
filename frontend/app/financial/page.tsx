import { ClientFinancialPage } from "@/components/ClientFinancialPage";
import { getFinancials } from "@/lib/api";

/**
 * Financial analysis page.
 */
export default async function FinancialPage(): Promise<JSX.Element> {
  const financials = await getFinancials("600519");

  return <ClientFinancialPage initialData={financials} />;
}
