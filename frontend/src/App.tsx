import { useState } from "react";

import { DashboardPage } from "./pages/DashboardPage";
import { CustomersPage } from "./pages/CustomersPage";
import { SegmentsPage } from "./pages/SegmentsPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { ExportPage } from "./pages/ExportPage";

import { PageShell } from "./components/layout/PageShell";

import type { PageName } from "./types/navigation";

function App() {
  const [currentPage, setCurrentPage] = useState<PageName>("Dashboard");

  return (
    <PageShell currentPage={currentPage} onPageChange={setCurrentPage}>
      {currentPage === "Dashboard" && <DashboardPage />}

      {currentPage === "Customers" && <CustomersPage />}

      {currentPage === "Segments" && <SegmentsPage />}

      {currentPage === "Recommendations" && <RecommendationsPage />}

      {currentPage === "Export" && <ExportPage />}
    </PageShell>
  );
}

export default App;