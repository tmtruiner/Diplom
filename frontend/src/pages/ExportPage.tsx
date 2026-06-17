import {
  BarChart3,
  Download,
  FileDown,
  Lightbulb,
  Table,
} from "lucide-react";

import {
  downloadExport,
  type ExportEndpoint,
} from "../services/exportApi";

import styles from "./ExportPage.module.css";

type ExportItem = {
  group: "Клиенты" | "Аналитика" | "Отчеты";
  title: string;
  purpose: string;
  fields: string[];
  fileName: string;
  format: "CSV";
  icon: React.ElementType;
  status: "Ready" | "Soon";
  endpoint: ExportEndpoint;
};

const exportItems: ExportItem[] = [
  {
    group: "Клиенты",
    title: "Клиенты высокого риска",
    purpose: "Список клиентов, с которыми нужно работать в первую очередь.",
    fields: ["ID клиента", "Вероятность оттока", "Фактор риска", "Выручка под риском", "Приоритет"],
    fileName: "high_risk_customers.csv",
    format: "CSV",
    icon: Table,
    status: "Ready",
    endpoint: "high-risk-customers",
  },
  {
    group: "Аналитика",
    title: "Сводка по сегментам",
    purpose: "Сравнение сегментов и подготовка управленческой сводки.",
    fields: ["Сегмент", "Клиенты", "Доля высокого риска", "Основное действие", "Основной фактор риска"],
    fileName: "segments_summary.csv",
    format: "CSV",
    icon: BarChart3,
    status: "Ready",
    endpoint: "segments",
  },
  {
    group: "Аналитика",
    title: "План рекомендаций",
    purpose: "Планирование действий по удержанию и оценка масштаба работ.",
    fields: ["Рекомендация", "Клиенты", "Клиенты высокого риска", "Выручка под риском", "Приоритет"],
    fileName: "recommendations_plan.csv",
    format: "CSV",
    icon: Lightbulb,
    status: "Ready",
    endpoint: "recommendations",
  },
  {
    group: "Отчеты",
    title: "Сводка дашборда",
    purpose: "Передача краткой сводки в отчет или электронную таблицу.",
    fields: ["Раздел", "Показатель", "Значение"],
    fileName: "dashboard_summary.csv",
    format: "CSV",
    icon: FileDown,
    status: "Ready",
    endpoint: "dashboard-summary",
  },
];

const groupedExportItems = exportItems.reduce<Record<ExportItem["group"], ExportItem[]>>(
  (groups, item) => {
    groups[item.group].push(item);
    return groups;
  },
  {
    Клиенты: [],
    Аналитика: [],
    Отчеты: [],
  }
);

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
        </div>
      </div>

      <div className={styles.exportDetails}>
        <div>
          <div className={styles.detailLabel}>Назначение</div>
          <p className={styles.detailText}>{item.purpose}</p>
        </div>

        <div>
          <div className={styles.detailLabel}>Состав данных</div>
          <div className={styles.fieldList}>
            {item.fields.map((field) => (
              <span key={field}>{field}</span>
            ))}
          </div>
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
            Выгрузка аналитических данных
          </p>
        </div>
      </header>

      {Object.entries(groupedExportItems).map(([group, items]) => (
        <section key={group} className={styles.exportGroup}>
          <div className={styles.exportGrid}>
            {items.map((item) => (
              <ExportCard key={item.title} item={item} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
