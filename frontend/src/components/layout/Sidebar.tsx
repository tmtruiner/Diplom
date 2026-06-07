import {
  BarChart3,
  FileDown,
  Info,
  Lightbulb,
  PieChart,
  Users,
} from "lucide-react";

import type { PageName } from "../../types/navigation";
import styles from "./Sidebar.module.css";

const pageItems: Array<{
  label: PageName;
  title: string;
  icon: React.ElementType;
}> = [
  { label: "Dashboard", title: "Дашборд", icon: PieChart },
  { label: "Customers", title: "Клиенты", icon: Users },
  { label: "Segments", title: "Сегменты", icon: BarChart3 },
  { label: "Recommendations", title: "Рекомендации", icon: Lightbulb },
  { label: "Export", title: "Выгрузки", icon: FileDown },
];

type SidebarProps = {
  currentPage: PageName;
  onPageChange: (page: PageName) => void;
  onOpenModelInfo: () => void;
};

export function Sidebar({
  currentPage,
  onPageChange,
  onOpenModelInfo,
}: SidebarProps) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoBlock}>
        <div className={styles.logo}>Churn Analytics</div>
        <div className={styles.logoSubtitle}>Платформа анализа оттока</div>
      </div>

      <nav className={styles.nav}>
        {pageItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.label;

          return (
            <button
              key={item.label}
              onClick={() => onPageChange(item.label)}
              className={`${styles.navItem} ${
                isActive ? styles.navItemActive : ""
              }`}
            >
              <Icon size={18} />
              {item.title}
            </button>
          );
        })}
      </nav>

      <div className={styles.sidebarFooter}>
        <button
          className={styles.modelInfoButton}
          onClick={onOpenModelInfo}
          title="Информация о модели"
        >
          <Info size={18} />
        </button>

        <div>
          <div className={styles.sidebarFooterText}>Техническая информация</div>
        </div>
      </div>
    </aside>
  );
}