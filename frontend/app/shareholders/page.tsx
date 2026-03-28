import { ClientShareholdersPage } from "@/components/ClientShareholdersPage";
import { getShareholders } from "@/lib/api";

/**
 * Shareholder analysis page.
 */
export default async function ShareholdersPage(): Promise<JSX.Element> {
  const shareholders = await getShareholders("600519");

  return <ClientShareholdersPage initialData={shareholders} />;
}
