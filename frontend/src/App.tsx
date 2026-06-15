import { useState } from "react";

import { DashboardPage } from "./pages/DashboardPage";
import { CustomersPage } from "./pages/CustomersPage";
import { SegmentsPage } from "./pages/SegmentsPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { ExportPage } from "./pages/ExportPage";

import { PageShell } from "./components/layout/PageShell";

import type { CustomerPageFilters } from "./types/customers";
import type { PageName } from "./types/navigation";

function App() {
  const [currentPage, setCurrentPage] = useState<PageName>("Dashboard");
  const [customerFilters, setCustomerFilters] = useState<CustomerPageFilters>(
    {}
  );
  const [customerViewKey, setCustomerViewKey] = useState(0);

  function openCustomers(filters: CustomerPageFilters = {}) {
    setCustomerFilters(filters);
    setCustomerViewKey((current) => current + 1);
    setCurrentPage("Customers");
  }

  function handlePageChange(page: PageName) {
    if (page === "Customers") {
      openCustomers();
      return;
    }

    setCurrentPage(page);
  }

  return (
    <PageShell currentPage={currentPage} onPageChange={handlePageChange}>
      {currentPage === "Dashboard" && (
        <DashboardPage onOpenCustomers={openCustomers} />
      )}

      {currentPage === "Customers" && (
        <CustomersPage
          key={customerViewKey}
          initialFilters={customerFilters}
        />
      )}

      {currentPage === "Segments" && (
        <SegmentsPage onOpenCustomers={openCustomers} />
      )}

      {currentPage === "Recommendations" && (
        <RecommendationsPage onOpenCustomers={openCustomers} />
      )}

      {currentPage === "Export" && <ExportPage />}
    </PageShell>
  );
}

export default App;
