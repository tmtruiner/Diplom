import { useState } from "react";
import type { ReactNode } from "react";

import type { PageName } from "../../types/navigation";
import { Sidebar } from "./Sidebar";
import { ModelInfoModal } from "./ModelInfoModal";
import styles from "./PageShell.module.css";

type PageShellProps = {
  currentPage: PageName;
  onPageChange: (page: PageName) => void;
  children: ReactNode;
};

export function PageShell({
  currentPage,
  onPageChange,
  children,
}: PageShellProps) {
  const [isModelInfoOpen, setIsModelInfoOpen] = useState(false);

  return (
    <div className={styles.appLayout}>
      <Sidebar
        currentPage={currentPage}
        onPageChange={onPageChange}
        onOpenModelInfo={() => setIsModelInfoOpen(true)}
      />

      <main className={styles.main}>{children}</main>

      <ModelInfoModal
        isOpen={isModelInfoOpen}
        onClose={() => setIsModelInfoOpen(false)}
      />
    </div>
  );
}