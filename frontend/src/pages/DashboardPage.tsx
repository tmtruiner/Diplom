import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Gauge,
  Lightbulb,
  ShieldAlert,
  Users,
} from "lucide-react";

import { fetchDashboardSummary } from "../services/dashboardApi";
import type { DashboardSummary } from "../types/dashboard";

import {
  translateRecommendation,
  translateRiskFactor,
  translateRiskGroup,
} from "../utils/displayLabels";

import styles from "./DashboardPage.module.css";

const riskColors = {
  Low: "#10b981",
  Medium: "#f59e0b",
  High: "#ef4444",
};

function formatNumber(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value);
}

function KpiCard({
  title,
  value,
  helper,
  icon: Icon,
  tone,
}: {
  title: string;
  value: string;
  helper?: string;
  icon: React.ElementType;
  tone: "blue" | "red" | "green" | "amber" | "violet";
}) {
  return (
    <div className={styles.kpiCard}>
      <div>
        <div className={styles.kpiTitle}>{title}</div>
        <div className={styles.kpiValue}>{value}</div>
        {helper && <div className={styles.kpiHelper}>{helper}</div>}
      </div>

      <div className={`${styles.kpiIcon} ${styles[tone]}`}>
        <Icon size={22} />
      </div>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className={styles.card}>
      <div className={styles.cardHeader}>
        <h2 className={styles.cardTitle}>{title}</h2>
        {subtitle && <p className={styles.cardSubtitle}>{subtitle}</p>}
      </div>

      {children}
    </section>
  );
}

function Badge({
  children,
  tone = "blue",
}: {
  children: React.ReactNode;
  tone?: "red" | "amber" | "green" | "blue" | "slate";
}) {
  return (
    <span className={`${styles.badge} ${styles[`badge_${tone}`]}`}>
      {children}
    </span>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    fetchDashboardSummary()
      .then((summary) => {
        setData(summary);
        setStatus("success");
      })
      .catch((error) => {
        setErrorMessage(error.message);
        setStatus("error");
      });
  }, []);

  if (status === "loading") {
    return (
      <div className={styles.page}>
        <div className={styles.stateBox}>Загрузка дашборда...</div>
      </div>
    );
  }

  if (status === "error" || !data) {
    return (
      <div className={styles.page}>
        <div className={styles.errorBox}>
          Не удалось загрузить дашборд: {errorMessage}
        </div>
      </div>
    );
  }

  const riskDistribution = data.risk_distribution.map((item) => ({
    name: translateRiskGroup(item.risk_group),
    value: item.customers_count,
    color: riskColors[item.risk_group],
  }));

  const activeRecommendationsCount = data.recommendations_summary
    .filter((item) => item.recommendation_type !== "No Action")
    .reduce((sum, item) => sum + item.customers_count, 0);

  const recommendationsSummary = data.recommendations_summary
    .filter((item) => item.recommendation_type !== "No Action")
    .map((item) => ({
      type: translateRecommendation(item.recommendation_type),
      originalType: item.recommendation_type,
      count: item.customers_count,
    }));

  const retentionPriorities = recommendationsSummary.slice(0, 4);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Дашборд</h1>
          <p className={styles.pageSubtitle}>
            Обзор оттока клиентов, факторов риска и приоритетов удержания
          </p>
        </div>
      </header>

      <section className={styles.kpiGrid}>
        <KpiCard
          title="Всего клиентов"
          value={formatNumber(data.kpis.total_customers)}
          helper="Последний скоринговый набор данных"
          icon={Users}
          tone="blue"
        />

        <KpiCard
          title="Клиенты высокого риска"
          value={formatNumber(data.kpis.high_risk_customers)}
          helper="Клиенты выше порога высокого риска"
          icon={ShieldAlert}
          tone="red"
        />

        <KpiCard
          title="Средняя вероятность оттока"
          value={data.kpis.average_churn_probability.toFixed(2)}
          helper="По всем скоринговым клиентам"
          icon={Gauge}
          tone="violet"
        />

        <KpiCard
          title="Активные рекомендации"
          value={formatNumber(activeRecommendationsCount)}
          helper="Клиенты, требующие действий по удержанию"
          icon={Lightbulb}
          tone="green"
        />
      </section>

      <section className={styles.topGrid}>
        <ChartCard
          title="Распределение по группам риска"
          subtitle="Клиенты с низким, средним и высоким риском оттока"
        >
          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={riskDistribution}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={130}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {riskDistribution.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <section className={styles.card}>
          <div className={styles.cardHeaderRow}>
            <div>
              <h2 className={styles.cardTitle}>Что сделать сегодня</h2>
              <p className={styles.cardSubtitle}>
                Основные действия, с которых стоит начать работу по удержанию
              </p>
            </div>

            <Badge tone="red">Требует действий</Badge>
          </div>

          <div className={styles.list}>
            {retentionPriorities.length > 0 ? (
              retentionPriorities.map((item, index) => (
                <div key={item.originalType} className={styles.riskFactorItem}>
                  <div className={styles.listLeft}>
                    <div className={styles.rank}>{index + 1}</div>

                    <div>
                      <div className={styles.listTitle}>{item.type}</div>
                      <div className={styles.listSubtitle}>
                        {formatNumber(item.count)} клиентов
                      </div>
                    </div>
                  </div>

                  <Badge tone={index === 0 ? "red" : "amber"}>
                    Приоритет
                  </Badge>
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>
                Активных действий по удержанию нет.
              </div>
            )}
          </div>
        </section>
      </section>

      <section className={styles.twoColumnGrid}>
        <ChartCard
          title="Сводка рекомендаций"
          subtitle="Действия по удержанию, сформированные на основе риска и правил"
        >
          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={recommendationsSummary}
                layout="vertical"
                margin={{ left: 120, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis
                  dataKey="type"
                  type="category"
                  width={240}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip />
                <Bar dataKey="count" fill="#7c3aed" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Главные факторы риска</h2>
            <p className={styles.cardSubtitle}>
              Наиболее частые причины среди клиентов высокого риска
            </p>
          </div>

          <div className={styles.list}>
            {data.top_risk_factors.map((item, index) => (
              <div key={item.factor} className={styles.riskFactorItem}>
                <div className={styles.listLeft}>
                  <div className={styles.rank}>{index + 1}</div>

                  <div>
                    <div className={styles.listTitle}>
                      {translateRiskFactor(item.factor)}
                    </div>
                    <div className={styles.listSubtitle}>
                      {formatNumber(item.customers_count)} клиентов высокого
                      риска
                    </div>
                  </div>
                </div>

                <Badge tone={item.impact === "High" ? "red" : "amber"}>
                  {item.impact === "High"
                    ? "Высокое влияние"
                    : "Среднее влияние"}
                </Badge>
              </div>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}