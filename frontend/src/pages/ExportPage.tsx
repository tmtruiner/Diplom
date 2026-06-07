import {
  BarChart3,
  Download,
  FileDown,
  Lightbulb,
  Table,
  Users,
} from "lucide-react";

import {
  downloadExport,
  type ExportEndpoint,
} from "../services/exportApi";

import styles from "./ExportPage.module.css";

type ExportItem = {
  title: string;
  description: string;
  fileName: string;
  format: "CSV" | "JSON";
  icon: React.ElementType;
  status: "Ready" | "Soon";
  endpoint: ExportEndpoint;
};

const exportItems: ExportItem[] = [
  {
    title: "Все клиенты",
    description:
      "Выгрузка таблицы клиентов с вероятностью оттока, группой риска, сегментом и рекомендацией.",
    fileName: "customers_export.csv",
    format: "CSV",
    icon: Users,
    status: "Ready",
    endpoint: "customers",
  },
  {
    title: "Клиенты высокого риска",
    description:
      "Выгрузка только клиентов из группы высокого риска для приоритизации действий по удержанию.",
    fileName: "high_risk_customers.csv",
    format: "CSV",
    icon: Table,
    status: "Ready",
    endpoint: "high-risk-customers",
  },
  {
    title: "Сводка по сегментам",
    description:
      "Выгрузка аналитики по сегментам: количество клиентов, средний риск, доля высокого риска и основное действие.",
    fileName: "segments_summary.csv",
    format: "CSV",
    icon: BarChart3,
    status: "Ready",
    endpoint: "segments",
  },
  {
    title: "План рекомендаций",
    description:
      "Выгрузка агрегированных действий по удержанию с количеством клиентов, метриками риска и выручкой под риском.",
    fileName: "recommendations_plan.csv",
    format: "CSV",
    icon: Lightbulb,
    status: "Ready",
    endpoint: "recommendations",
  },
  {
    title: "Сводка дашборда",
    description:
      "Выгрузка текущих KPI и верхнеуровневых метрик дашборда для отчётности.",
    fileName: "dashboard_summary.json",
    format: "JSON",
    icon: FileDown,
    status: "Ready",
    endpoint: "dashboard-summary",
  },
];

function translateStatus(status: ExportItem["status"]) {
  if (status === "Ready") return "Готово";
  if (status === "Soon") return "Скоро";
  return status;
}

function Badge({
  children,
  tone = "blue",
}: {
  children: React.ReactNode;
  tone?: "blue" | "green" | "slate";
}) {
  return (
    <span className={`${styles.badge} ${styles[`badge_${tone}`]}`}>
      {children}
    </span>
  );
}

function ExportCard({ item }: { item: ExportItem }) {
  const Icon = item.icon;
  const isReady = item.status === "Ready";

  function handleClick() {
    if (!isReady) {
      return;
    }

    downloadExport(item.endpoint);
  }

  return (
    <section className={styles.exportCard}>
      <div className={styles.exportHeader}>
        <div className={styles.iconBox}>
          <Icon size={22} />
        </div>

        <div className={styles.exportMeta}>
          <h2 className={styles.exportTitle}>{item.title}</h2>
          <p className={styles.exportDescription}>{item.description}</p>
        </div>
      </div>

      <div className={styles.exportFooter}>
        <div>
          <div className={styles.fileLabel}>Файл</div>
          <div className={styles.fileName}>{item.fileName}</div>
        </div>

        <div className={styles.footerRight}>
          <Badge tone={item.status === "Ready" ? "green" : "slate"}>
            {translateStatus(item.status)}
          </Badge>

          <Badge tone="blue">{item.format}</Badge>

          <button
            className={styles.downloadButton}
            disabled={!isReady}
            onClick={handleClick}
          >
            <Download size={16} />
            Скачать
          </button>
        </div>
      </div>
    </section>
  );
}

export function ExportPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Выгрузки</h1>
          <p className={styles.pageSubtitle}>
            Скачивание аналитических наборов данных, списков клиентов и отчётов по удержанию.
          </p>
        </div>
      </header>

      <section className={styles.exportGrid}>
        {exportItems.map((item) => (
          <ExportCard key={item.title} item={item} />
        ))}
      </section>
    </div>
  );
}