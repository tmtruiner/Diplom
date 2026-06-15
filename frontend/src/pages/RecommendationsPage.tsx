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

import { fetchRecommendations } from "../services/recommendationsApi";
import type { CustomerPageFilters } from "../types/customers";
import type { RecommendationItem } from "../types/recommendations";

import {
  translatePriority,
  translateRecommendation,
  translateRiskFactor,
  translateRecommendationReason,
} from "../utils/displayLabels";

import styles from "./RecommendationsPage.module.css";

function formatNumber(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value);
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function getPriorityTone(priority: string | null) {
  if (priority === "High") return "red";
  if (priority === "Medium") return "amber";
  if (priority === "Low") return "green";
  return "slate";
}

function getRiskToneByProbability(probability: number) {
  if (probability >= 0.7) return "red";
  if (probability >= 0.35) return "amber";
  return "green";
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

function RecommendationProfilePanel({
  recommendation,
  onOpenCustomers,
}: {
  recommendation: RecommendationItem | null;
  onOpenCustomers: (filters: CustomerPageFilters) => void;
}) {
  if (!recommendation) {
    return (
      <aside className={styles.detailsPanel}>
        <div className={styles.emptyState}>Выберите рекомендацию</div>
      </aside>
    );
  }

  return (
    <aside className={styles.detailsPanel}>
      <div className={styles.detailsHeader}>
        <div>
          <div className={styles.detailsLabel}>Выбранное действие</div>
          <h2 className={styles.detailsTitle}>
            {translateRecommendation(recommendation.recommendation_type)}
          </h2>
        </div>
      </div>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Метрики действия</h3>

        <div className={styles.detailBox}>
          <div className={styles.detailRow}>
            <span>Клиенты</span>
            <strong>{formatNumber(recommendation.customers_count)}</strong>
          </div>

          <div className={styles.detailRow}>
            <span>Клиенты высокого риска</span>
            <strong>
              {formatNumber(recommendation.high_risk_customers)}
            </strong>
          </div>

          <div className={styles.detailRow}>
            <span>Доля высокого риска</span>
            <strong>
              {Math.round(recommendation.high_risk_share * 100)}%
            </strong>
          </div>

          <div className={styles.detailRow}>
            <span>Средняя вероятность оттока</span>
            <strong>
              {recommendation.average_churn_probability.toFixed(2)}
            </strong>
          </div>

          <div className={styles.detailRow}>
            <span>Выручка под риском</span>
            <strong>
              {formatMoney(recommendation.estimated_revenue_at_risk)}
            </strong>
          </div>
        </div>
      </section>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Главный фактор риска</h3>
        <div className={styles.infoBox}>
          {translateRiskFactor(recommendation.main_risk_factor)}
        </div>
      </section>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Логика рекомендации</h3>
        <div className={styles.recommendationBox}>
            {translateRecommendationReason(recommendation.recommendation_reason)}
        </div>
      </section>

      <div className={styles.panelActions}>
        <button
          type="button"
          className={styles.secondaryActionButton}
          onClick={() =>
            onOpenCustomers({
              recommendation: recommendation.recommendation_type,
            })
          }
        >
          Показать клиентов с рекомендацией
        </button>
      </div>
    </aside>
  );
}

type RecommendationsPageProps = {
  onOpenCustomers: (filters: CustomerPageFilters) => void;
};

export function RecommendationsPage({
  onOpenCustomers,
}: RecommendationsPageProps) {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>(
    []
  );

  const [selectedRecommendationType, setSelectedRecommendationType] = useState<
    string | null
  >(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsLoading(true);
    setError("");

    fetchRecommendations()
      .then((response) => {
        const activeItems = response.items.filter(
          (item) => item.recommendation_type !== "No Action"
        );

        setRecommendations(activeItems);

        if (activeItems.length > 0) {
          setSelectedRecommendationType(activeItems[0].recommendation_type);
        }
      })
      .catch((error) => {
        setError(error.message);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const selectedRecommendation =
    recommendations.find(
      (item) => item.recommendation_type === selectedRecommendationType
    ) ?? null;

  const chartData = recommendations.map((item) => ({
    type: translateRecommendation(item.recommendation_type),
    originalType: item.recommendation_type,
    customers: item.customers_count,
  }));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Рекомендации</h1>
          <p className={styles.pageSubtitle}>
            Очереди действий по удержанию клиентов и приоритизация работы.
          </p>
        </div>
      </header>

      {error && (
        <div className={styles.errorBox}>
          Не удалось загрузить рекомендации: {error}
        </div>
      )}

      <section className={styles.chartsGrid}>
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Объём рекомендаций</h2>
            <p>
              Сколько клиентов назначено на каждое действие по удержанию.
            </p>
          </div>

          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ left: 120, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis
                  dataKey="type"
                  type="category"
                  width={260}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip />
                <Bar dataKey="customers" radius={[0, 8, 8, 0]}>
                  {chartData.map((entry) => (
                    <Cell
                      key={entry.originalType}
                      fill="#7c3aed"
                      cursor="pointer"
                      onClick={() =>
                        onOpenCustomers({
                          recommendation: entry.originalType,
                        })
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Приоритет действий</h2>
            <p>Рекомендации, отсортированные по бизнес-значимости.</p>
          </div>

          <div className={styles.priorityList}>
            {recommendations.slice(0, 5).map((item, index) => (
              <button
                type="button"
                key={item.recommendation_type}
                className={`${styles.priorityItem} ${styles.clickableListItem}`}
                onClick={() =>
                  onOpenCustomers({
                    recommendation: item.recommendation_type,
                  })
                }
              >
                <div className={styles.priorityLeft}>
                  <div className={styles.rank}>{index + 1}</div>

                  <div>
                    <div className={styles.priorityTitle}>
                      {translateRecommendation(item.recommendation_type)}
                    </div>
                    <div className={styles.prioritySubtitle}>
                      {formatNumber(item.customers_count)} клиентов ·{" "}
                      {Math.round(item.high_risk_share * 100)}% высокого риска
                    </div>
                  </div>
                </div>

                <Badge tone={getPriorityTone(item.priority)}>
                  {translatePriority(item.priority)}
                </Badge>
              </button>
            ))}
          </div>
        </section>
      </section>

      <section className={styles.contentGrid}>
        <section className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <div>
              <h2>План рекомендаций</h2>
              <p>
                {isLoading
                  ? "Загрузка рекомендаций..."
                  : `Загружено активных типов рекомендаций: ${recommendations.length}`}
              </p>
            </div>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Рекомендация</th>
                  <th>Клиенты</th>
                  <th>Доля высокого риска</th>
                  <th>Средний риск</th>
                  <th>Выручка под риском</th>
                  <th>Приоритет</th>
                </tr>
              </thead>

              <tbody>
                {recommendations.map((item) => {
                  const isSelected =
                    item.recommendation_type === selectedRecommendationType;

                  return (
                    <tr
                      key={item.recommendation_type}
                      className={isSelected ? styles.selectedRow : ""}
                      onClick={() =>
                        setSelectedRecommendationType(item.recommendation_type)
                      }
                    >
                      <td className={styles.recommendationNameCell}>
                        <button
                          type="button"
                          className={styles.linkLikeButton}
                          onClick={(event) => {
                            event.stopPropagation();
                            onOpenCustomers({
                              recommendation: item.recommendation_type,
                            });
                          }}
                        >
                          {translateRecommendation(item.recommendation_type)}
                        </button>
                      </td>

                      <td>{formatNumber(item.customers_count)}</td>

                      <td>{Math.round(item.high_risk_share * 100)}%</td>

                      <td>
                        <Badge
                          tone={getRiskToneByProbability(
                            item.average_churn_probability
                          )}
                        >
                          {item.average_churn_probability.toFixed(2)}
                        </Badge>
                      </td>

                      <td>{formatMoney(item.estimated_revenue_at_risk)}</td>

                      <td>
                        <Badge tone={getPriorityTone(item.priority)}>
                          {translatePriority(item.priority)}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {!isLoading && recommendations.length === 0 && (
              <div className={styles.emptyState}>
                Активные рекомендации не найдены.
              </div>
            )}
          </div>
        </section>

        <RecommendationProfilePanel
          recommendation={selectedRecommendation}
          onOpenCustomers={onOpenCustomers}
        />
      </section>
    </div>
  );
}
