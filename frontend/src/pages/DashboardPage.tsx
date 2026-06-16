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
import type { CustomerPageFilters } from "../types/customers";
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

function getRecommendationChartLabel(value: string | null | undefined) {
  const map: Record<string, string> = {
    "Service Recovery Call": "Восстановление сервиса",
    "Tariff Optimization": "Оптимизация тарифа",
    "Voice Mail Offer": "Голосовая почта",
    "Voice Mail Plan Offer": "Голосовая почта",
    "Retention Discount": "Скидка на удержание",
    "International Plan Review": "Международный тариф",
  };

  if (!value) {
    return "-";
  }

  return map[value] ?? translateRecommendation(value);
}

function translateImpact(value: "Low" | "Medium" | "High") {
  if (value === "High") return "Высокое влияние";
  if (value === "Medium") return "Среднее влияние";
  return "Низкое влияние";
}

function getImpactTone(value: "Low" | "Medium" | "High") {
  if (value === "High") return "red";
  if (value === "Medium") return "amber";
  return "green";
}

function KpiCard({
  title,
  value,
  icon: Icon,
  tone,
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  tone: "blue" | "red" | "green" | "amber" | "violet";
}) {
  return (
    <section className={styles.kpiCard}>
      <div>
        <div className={styles.kpiTitle}>{title}</div>
        <div className={styles.kpiValue}>{value}</div>
      </div>

      <div className={`${styles.kpiIcon} ${styles[tone]}`}>
        <Icon size={22} />
      </div>
    </section>
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

type DashboardPageProps = {
  onOpenCustomers: (filters?: CustomerPageFilters) => void;
};

export function DashboardPage({
  onOpenCustomers,
}: DashboardPageProps) {
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
    originalRiskGroup: item.risk_group,
    value: item.customers_count,
    color: riskColors[item.risk_group],
  }));

  const activeRecommendationsCount = data.recommendations_summary
    .filter((item) => item.recommendation_type !== "No Action")
    .reduce((sum, item) => sum + item.customers_count, 0);

  const recommendationsSummary = data.recommendations_summary
    .filter((item) => item.recommendation_type !== "No Action")
    .map((item) => ({
      type: getRecommendationChartLabel(item.recommendation_type),
      fullType: translateRecommendation(item.recommendation_type),
      originalType: item.recommendation_type,
      count: item.customers_count,
    }));
  const maxRecommendationCount = Math.max(
    1,
    ...recommendationsSummary.map((item) => item.count)
  );

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
          icon={Users}
          tone="blue"
        />

        <KpiCard
          title="Клиенты высокого риска"
          value={formatNumber(data.kpis.high_risk_customers)}
          icon={ShieldAlert}
          tone="red"
        />

        <KpiCard
          title="Средняя вероятность оттока"
          value={data.kpis.average_churn_probability.toFixed(2)}
          icon={Gauge}
          tone="violet"
        />

        <KpiCard
          title="Активные рекомендации"
          value={formatNumber(activeRecommendationsCount)}
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
                    <Cell
                      key={entry.name}
                      fill={entry.color}
                      cursor="pointer"
                      onClick={() =>
                        onOpenCustomers({
                          riskGroup: entry.originalRiskGroup,
                        })
                      }
                    />
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
                <button
                  type="button"
                  key={item.originalType}
                  className={`${styles.riskFactorItem} ${styles.clickableListItem}`}
                  onClick={() =>
                    onOpenCustomers({
                      recommendation: item.originalType,
                    })
                  }
                >
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
                </button>
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
          <div className={styles.barListChart}>
            {recommendationsSummary.length > 0 ? (
              recommendationsSummary.map((entry) => (
                <button
                  type="button"
                  key={entry.originalType}
                  className={styles.barChartRow}
                  onClick={() =>
                    onOpenCustomers({
                      recommendation: entry.originalType,
                    })
                  }
                  title={entry.fullType}
                >
                  <span className={styles.barChartLabel}>
                    {entry.type}
                  </span>
                  <span className={styles.barChartTrack}>
                    <span
                      className={styles.barChartFill}
                      style={{
                        width: `${Math.max(
                          2,
                          (entry.count / maxRecommendationCount) * 100
                        )}%`,
                      }}
                    />
                  </span>
                  <span className={styles.barChartValue}>
                    {formatNumber(entry.count)}
                  </span>
                </button>
              ))
            ) : (
              <div className={styles.emptyState}>
                Активных рекомендаций нет.
              </div>
            )}
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
              <button
                type="button"
                key={item.factor}
                className={`${styles.riskFactorItem} ${styles.clickableListItem}`}
                onClick={() =>
                  onOpenCustomers({
                    mainRiskFactor: item.factor,
                  })
                }
              >
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

                <Badge tone={getImpactTone(item.impact)}>
                  {translateImpact(item.impact)}
                </Badge>
              </button>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}
