import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


import { fetchSegments } from "../services/segmentsApi";
import type { SegmentItem } from "../types/segments";

import {
  translateRecommendation,
  translateRiskFactor,
  translateSegment,
} from "../utils/displayLabels";

import styles from "./SegmentsPage.module.css";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value);
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

function SegmentProfilePanel({
  segment,
}: {
  segment: SegmentItem | null;
}) {
  if (!segment) {
    return (
      <aside className={styles.detailsPanel}>
        <div className={styles.emptyState}>Выберите сегмент</div>
      </aside>
    );
  }

  return (
    <aside className={styles.detailsPanel}>
      <div className={styles.detailsHeader}>
        <div>
          <div className={styles.detailsLabel}>Выбранный сегмент</div>
          <h2 className={styles.detailsTitle}>
            {translateSegment(segment.segment_name)}
          </h2>
        </div>
      </div>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Метрики сегмента</h3>

        <div className={styles.detailBox}>
          <div className={styles.detailRow}>
            <span>Количество клиентов</span>
            <strong>{formatNumber(segment.clients_count)}</strong>
          </div>

          <div className={styles.detailRow}>
            <span>Средняя вероятность оттока</span>
            <strong>{segment.average_churn_probability.toFixed(2)}</strong>
          </div>

          <div className={styles.detailRow}>
            <span>Доля клиентов высокого риска</span>
            <strong>{Math.round(segment.high_risk_share * 100)}%</strong>
          </div>

          <div className={styles.detailRow}>
            <span>Средние оценочные расходы</span>
            <strong>
              {formatMoney(segment.average_estimated_total_charge)}
            </strong>
          </div>
        </div>
      </section>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Главный фактор риска</h3>
        <div className={styles.infoBox}>
          {translateRiskFactor(segment.main_risk_factor)}
        </div>
      </section>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Рекомендуемое действие</h3>
        <div className={styles.recommendationBox}>
          {translateRecommendation(segment.main_recommendation)}
        </div>
      </section>
    </aside>
  );
}

export function SegmentsPage() {
  const [segments, setSegments] = useState<SegmentItem[]>([]);
  const [selectedSegmentName, setSelectedSegmentName] = useState<string | null>(
    null
  );

  const [isLoadingSegments, setIsLoadingSegments] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsLoadingSegments(true);
    setError("");

    fetchSegments()
      .then((response) => {
        setSegments(response.items);

        if (response.items.length > 0) {
          setSelectedSegmentName(response.items[0].segment_name);
        }
      })
      .catch((error) => {
        setError(error.message);
      })
      .finally(() => {
        setIsLoadingSegments(false);
      });
  }, []);

  const selectedSegment =
    segments.find((segment) => segment.segment_name === selectedSegmentName) ??
    null;

  const avgRiskChartData = segments.map((segment) => ({
    segment: translateSegment(segment.segment_name),
    risk: segment.average_churn_probability,
  }));

  const highRiskShareChartData = segments.map((segment) => ({
    segment: translateSegment(segment.segment_name),
    share: Math.round(segment.high_risk_share * 100),
  }));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Сегменты</h1>
          <p className={styles.pageSubtitle}>
            Сравнение групп клиентов, уровня риска и логики удержания.
          </p>
        </div>
      </header>

      {error && (
        <div className={styles.errorBox}>
          Не удалось загрузить сегменты: {error}
        </div>
      )}

      <section className={styles.chartsGrid}>
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Средняя вероятность оттока по сегментам</h2>
            <p>Показывает, какие группы клиентов чаще склонны к оттоку.</p>
          </div>

          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={avgRiskChartData}
                layout="vertical"
                margin={{ left: 110, right: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 1]} />
                <YAxis
                  dataKey="segment"
                  type="category"
                  width={240}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip formatter={(value) => Number(value).toFixed(2)} />
                <Bar dataKey="risk" fill="#2563eb" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Доля клиентов высокого риска по сегментам</h2>
            <p>Показывает концентрацию high-risk клиентов внутри группы.</p>
          </div>

          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={highRiskShareChartData}
                margin={{ left: 10, right: 20, bottom: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="segment"
                  angle={-18}
                  textAnchor="end"
                  height={95}
                  tick={{ fontSize: 12 }}
                />
                <YAxis unit="%" />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="share" fill="#ef4444" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </section>

      <section className={styles.contentGrid}>
        <section className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <div>
              <h2>Сравнение сегментов</h2>
              <p>
                {isLoadingSegments
                  ? "Загрузка сегментов..."
                  : `Загружено сегментов: ${segments.length}`}
              </p>
            </div>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Сегмент</th>
                  <th>Клиенты</th>
                  <th>Средний риск</th>
                  <th>Доля высокого риска</th>
                  <th>Действие</th>
                </tr>
              </thead>

              <tbody>
                {segments.map((segment) => {
                  const isSelected =
                    segment.segment_name === selectedSegmentName;

                  return (
                    <tr
                      key={segment.segment_name}
                      className={isSelected ? styles.selectedRow : ""}
                      onClick={() =>
                        setSelectedSegmentName(segment.segment_name)
                      }
                    >
                      <td className={styles.segmentNameCell}>
                        <div>{translateSegment(segment.segment_name)}</div>
                      </td>

                      <td>{formatNumber(segment.clients_count)}</td>

                      <td>
                        <Badge
                          tone={getRiskToneByProbability(
                            segment.average_churn_probability
                          )}
                        >
                          {segment.average_churn_probability.toFixed(2)}
                        </Badge>
                      </td>

                      <td>{Math.round(segment.high_risk_share * 100)}%</td>

                      <td>
                        {translateRecommendation(segment.main_recommendation)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {!isLoadingSegments && segments.length === 0 && (
              <div className={styles.emptyState}>Сегменты не найдены.</div>
            )}
          </div>
        </section>

        <SegmentProfilePanel segment={selectedSegment} />
      </section>
    </div>
  );
}