import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { fetchSegments } from "../services/segmentsApi";
import type { CustomerPageFilters } from "../types/customers";
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

function getNormalizedPercentAxisMax(values: number[]) {
  const maxValue = Math.max(0, ...values);
  const roundedMax = Math.ceil(maxValue / 5) * 5;

  return Math.min(100, Math.max(20, roundedMax + 5));
}

function getNormalizedCountAxisDomain(values: number[]): [number, number] {
  if (values.length === 0) {
    return [0, 100];
  }

  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const spread = Math.max(maxValue - minValue, maxValue * 0.1, 100);
  const padding = spread * 0.15;
  const step = spread >= 1000 ? 500 : 100;

  const minDomain = Math.max(0, Math.floor((minValue - padding) / step) * step);
  const maxDomain = Math.ceil((maxValue + padding) / step) * step;

  return [minDomain, maxDomain];
}

function getRiskToneByProbability(probability: number) {
  if (probability >= 0.7) return "red";
  if (probability >= 0.35) return "amber";
  return "green";
}

function getHighRiskShareTone(share: number) {
  if (share >= 0.5) return "red";
  if (share >= 0.15) return "amber";
  return "green";
}

function getAttentionLevel(segment: SegmentItem) {
  if (
    segment.average_churn_probability >= 0.7 ||
    segment.high_risk_share >= 0.5 ||
    segment.high_risk_customers >= 10
  ) {
    return {
      label: "Критический приоритет",
      tone: "red" as const,
      color: "#ef4444",
    };
  }

  if (
    segment.average_churn_probability >= 0.35 ||
    segment.high_risk_share >= 0.15 ||
    segment.high_risk_customers >= 3
  ) {
    return {
      label: "Требует внимания",
      tone: "amber" as const,
      color: "#f59e0b",
    };
  }

  return {
    label: "Стабильный сегмент",
    tone: "green" as const,
    color: "#10b981",
  };
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

type PriorityMapPoint = {
  segment_name: string;
  display_name: string;
  clients: number;
  highRiskShare: number;
  highRiskCustomers: number;
  averageRisk: number;
  charge: number;
  color: string;
};

function PriorityMapTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: PriorityMapPoint }>;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0].payload;

  return (
    <div className={styles.chartTooltip}>
      <strong>{point.display_name}</strong>
      <span>{formatNumber(point.clients)} клиентов</span>
      <span>
        Высокий риск: {formatNumber(point.highRiskCustomers)} /{" "}
        {point.highRiskShare}%
      </span>
      <span>Средняя вероятность ухода: {point.averageRisk.toFixed(2)}</span>
      <span>Средние расходы: {formatMoney(point.charge)}</span>
    </div>
  );
}

function SegmentProfilePanel({
  segment,
  portfolioAverageRisk,
}: {
  segment: SegmentItem | null;
  portfolioAverageRisk: number;
}) {
  if (!segment) {
    return (
      <aside className={styles.detailsPanel}>
        <div className={styles.emptyState}>Выберите сегмент</div>
      </aside>
    );
  }

  const attention = getAttentionLevel(segment);
  const riskDifference =
    segment.average_churn_probability - portfolioAverageRisk;
  const riskDifferencePercent = Math.round(Math.abs(riskDifference) * 100);

  let comparisonText = "Риск соответствует среднему уровню по клиентской базе.";

  if (riskDifferencePercent > 0) {
    comparisonText =
      riskDifference > 0
        ? `Вероятность ухода на ${riskDifferencePercent} п.п. выше среднего по клиентской базе.`
        : `Вероятность ухода на ${riskDifferencePercent} п.п. ниже среднего по клиентской базе.`;
  }

  return (
    <aside className={styles.detailsPanel}>
      <div className={styles.detailsHeader}>
        <div>
          <div className={styles.detailsLabel}>Профиль сегмента</div>
          <h2 className={styles.detailsTitle}>
            {translateSegment(segment.segment_name)}
          </h2>
        </div>
      </div>

      <Badge tone={attention.tone}>{attention.label}</Badge>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Почему она важна</h3>
        <div className={styles.insightBox}>
          <strong>{comparisonText}</strong>
          <span>
            {segment.high_risk_customers > 0
              ? `${formatNumber(segment.high_risk_customers)} клиентов уже находятся в группе высокого риска.`
              : "Клиентов высокого риска в этом сегменте сейчас нет."}
          </span>
        </div>
      </section>

      <section className={styles.detailsSection}>
        <h3 className={styles.detailsSectionTitle}>Масштаб сегмента</h3>
        <div className={styles.compactMetrics}>
          <div>
            <span>Клиенты</span>
            <strong>{formatNumber(segment.clients_count)}</strong>
          </div>
          <div>
            <span>Высокий риск</span>
            <strong>
              {formatNumber(segment.high_risk_customers)} /{" "}
              {Math.round(segment.high_risk_share * 100)}%
            </strong>
          </div>
          <div>
            <span>Средние расходы</span>
            <strong>{formatMoney(segment.average_estimated_total_charge)}</strong>
          </div>
        </div>
      </section>
    </aside>
  );
}

type SegmentsPageProps = {
  onOpenCustomers: (filters: CustomerPageFilters) => void;
};

export function SegmentsPage({ onOpenCustomers }: SegmentsPageProps) {
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
    segments[0] ??
    null;
  const effectiveSelectedSegmentName = selectedSegment?.segment_name ?? null;

  const totalCustomers = segments.reduce(
    (sum, segment) => sum + segment.clients_count,
    0
  );
  const portfolioAverageRisk =
    totalCustomers > 0
      ? segments.reduce(
          (sum, segment) =>
            sum +
            segment.average_churn_probability * segment.clients_count,
          0
        ) / totalCustomers
      : 0;

  const priorityMapData: PriorityMapPoint[] = segments.map((segment) => ({
    segment_name: segment.segment_name,
    display_name: translateSegment(segment.segment_name),
    clients: segment.clients_count,
    highRiskShare: Math.round(segment.high_risk_share * 100),
    highRiskCustomers: segment.high_risk_customers,
    averageRisk: segment.average_churn_probability,
    charge: segment.average_estimated_total_charge,
    color: getAttentionLevel(segment).color,
  }));
  const highRiskShareAxisMax = getNormalizedPercentAxisMax(
    priorityMapData.map((point) => point.highRiskShare)
  );
  const clientsAxisDomain = getNormalizedCountAxisDomain(
    priorityMapData.map((point) => point.clients)
  );

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Сегменты клиентов</h1>
          <p className={styles.pageSubtitle}>
            Сравнение масштаба и риска для групп
            клиентов.
          </p>
        </div>
      </header>

      {error && (
        <div className={styles.errorBox}>
          Не удалось загрузить сегменты: {error}
        </div>
      )}

      <section className={styles.mapSection}>
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2>Карта сегментов</h2>
            <p>
              Чем выше точка, тем больше доля клиентов высокого риска; чем
              правее, тем больше клиентов в сегменте. Шкала риска подстраивается
              под текущую выборку.
            </p>
          </div>

          <div className={styles.priorityMap}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 16, right: 24, bottom: 16, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="clients"
                  name="Клиенты"
                  domain={clientsAxisDomain}
                  allowDataOverflow={false}
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  type="number"
                  dataKey="highRiskShare"
                  name="Доля высокого риска"
                  unit="%"
                  domain={[0, highRiskShareAxisMax]}
                  tick={{ fontSize: 12 }}
                />
                <ZAxis
                  type="number"
                  dataKey="charge"
                  range={[100, 550]}
                  name="Средние расходы"
                />
                <ReferenceLine y={15} stroke="#f59e0b" strokeDasharray="5 5" />
                {highRiskShareAxisMax >= 50 && (
                  <ReferenceLine
                    y={50}
                    stroke="#ef4444"
                    strokeDasharray="5 5"
                  />
                )}
                <Tooltip content={<PriorityMapTooltip />} />
                <Scatter data={priorityMapData}>
                  {priorityMapData.map((entry) => (
                    <Cell
                      key={entry.segment_name}
                      fill={entry.color}
                      cursor="pointer"
                      stroke={
                        entry.segment_name === effectiveSelectedSegmentName
                          ? "#0f172a"
                          : "#ffffff"
                      }
                      strokeWidth={
                        entry.segment_name === effectiveSelectedSegmentName
                          ? 3
                          : 1
                      }
                      onClick={() =>
                        setSelectedSegmentName(entry.segment_name)
                      }
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className={styles.chartLegend}>
            <span>
              <i className={styles.legendRed} /> Критический приоритет
            </span>
            <span>
              <i className={styles.legendAmber} /> Требует внимания
            </span>
            <span>
              <i className={styles.legendGreen} /> Стабильный сегмент
            </span>
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
                  : `Показано сегментов: ${segments.length}`}
              </p>
            </div>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Сегмент</th>
                  <th>Клиенты</th>
                  <th>Высокий риск</th>
                  <th>Средняя вероятность</th>
                  <th>Основная проблема</th>
                  <th>Действие</th>
                </tr>
              </thead>

              <tbody>
                {segments.map((segment) => {
                  const isSelected =
                    segment.segment_name === effectiveSelectedSegmentName;

                  return (
                    <tr
                      key={segment.segment_name}
                      className={isSelected ? styles.selectedRow : ""}
                      onClick={() =>
                        setSelectedSegmentName(segment.segment_name)
                      }
                    >
                      <td className={styles.segmentNameCell}>
                        <button
                          type="button"
                          className={styles.linkLikeButton}
                          onClick={(event) => {
                            event.stopPropagation();
                            onOpenCustomers({ segment: segment.segment_name });
                          }}
                        >
                          {translateSegment(segment.segment_name)}
                        </button>
                      </td>
                      <td>{formatNumber(segment.clients_count)}</td>
                      <td>
                        <Badge tone={getHighRiskShareTone(segment.high_risk_share)}>
                          {formatNumber(segment.high_risk_customers)} /{" "}
                          {Math.round(segment.high_risk_share * 100)}%
                        </Badge>
                      </td>
                      <td>
                        <Badge
                          tone={getRiskToneByProbability(
                            segment.average_churn_probability
                          )}
                        >
                          {segment.average_churn_probability.toFixed(2)}
                        </Badge>
                      </td>
                      <td>{translateRiskFactor(segment.main_risk_factor)}</td>
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

        <SegmentProfilePanel
          segment={selectedSegment}
          portfolioAverageRisk={portfolioAverageRisk}
        />
      </section>
    </div>
  );
}
