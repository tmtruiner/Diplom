import { useEffect, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Search,
  SlidersHorizontal,
  Target,
  UserRound,
  ChevronDown,
  Download,
} from "lucide-react";

import {
  fetchCustomerDetail,
  fetchCustomerFilterOptions,
  fetchCustomers,
} from "../services/customersApi";
import { downloadFilteredCustomers } from "../services/exportApi";


import type {
  CustomerDetail,
  CustomerFilterOptions,
  CustomerListItem,
  CustomerPageFilters,
} from "../types/customers";

import {
  translateRecommendation,
  translateRecommendationReason,
  translatePriority,
  translateRiskFactor,
  translateRiskGroup,
  translateSegment,
} from "../utils/displayLabels";

import styles from "./CustomersPage.module.css";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function getRiskTone(riskGroup: string) {
  if (riskGroup === "High") return "red";
  if (riskGroup === "Medium") return "amber";
  return "green";
}

function getHealthColor(tone: string) {
  if (tone === "red") return "#ef4444";
  if (tone === "amber") return "#f59e0b";
  if (tone === "green") return "#10b981";
  return "#2563eb";
}

function formatDate(value?: string | null) {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU").format(date);
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

type SelectOption = {
  value: string;
  label: string;
};

function CustomSelect({
  value,
  options,
  onChange,
}: {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef<HTMLDivElement | null>(null);

  const selectedOption =
    options.find((option) => option.value === value) ?? options[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        selectRef.current &&
        !selectRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className={styles.customSelect} ref={selectRef}>
      <button
        type="button"
        className={`${styles.customSelectButton} ${
          isOpen ? styles.customSelectButtonOpen : ""
        }`}
        onClick={() => setIsOpen((current) => !current)}
      >
        <span className={styles.customSelectValue}>
          {selectedOption?.label ?? "Выберите значение"}
        </span>

        <ChevronDown
          size={16}
          className={`${styles.customSelectIcon} ${
            isOpen ? styles.customSelectIconOpen : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className={styles.customSelectMenu}>
          {options.map((option) => {
            const isActive = option.value === value;

            return (
              <button
                key={option.value}
                type="button"
                className={`${styles.customSelectOption} ${
                  isActive ? styles.customSelectOptionActive : ""
                }`}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CustomerDetailsPanel({
  customer,
}: {
  customer: CustomerDetail | null;
}) {
  if (!customer) {
    return (
      <aside className={styles.detailsPanel}>
        <div className={styles.emptyState}>Выберите клиента</div>
      </aside>
    );
  }

  const health = customer.health;
  const healthColor = getHealthColor(health.status.tone);
  const nextAction = health.next_best_action;
  const riskFactor = customer.prediction.main_risk_factor;
  const hasActionableRiskFactor =
    riskFactor && riskFactor !== "Stable customer profile";

  return (
    <aside className={styles.detailsPanel}>
      <div className={styles.healthHeader}>
        <div>
          <div className={styles.detailsLabel}>Состояние клиента</div>
          <h2 className={styles.detailsTitle}>{customer.customer_id}</h2>
        </div>

        <div className={styles.healthHeaderIcon}>
          <Activity size={18} />
        </div>
      </div>

      <section className={styles.healthHero}>
        <div
          className={styles.healthScoreCircle}
          style={
            {
              "--health-progress": `${health.score * 3.6}deg`,
              "--health-color": healthColor,
            } as React.CSSProperties
          }
        >
          <div className={styles.healthScoreInner}>
            <strong>{health.score}</strong>
            <span>/100</span>
          </div>
        </div>

        <div className={styles.healthHeroContent}>
          <div className={styles.healthHeroLabel}>Оценка состояния</div>

          <span
            className={`${styles.healthStatusBadge} ${
              styles[`healthStatusBadge_${health.status.tone}`]
            }`}
          >
            {health.status.label}
          </span>

          <div className={styles.healthDate}>
            Прогноз от {formatDate(customer.prediction.scoring_date)}
          </div>
        </div>
      </section>

      <section className={styles.healthSection}>
        <h3 className={styles.healthSectionTitle}>
          <AlertTriangle size={15} />
          Почему требуется внимание
        </h3>

        <div className={styles.riskReasonBox}>
          <div className={styles.riskReasonTitle}>
            {hasActionableRiskFactor
              ? translateRiskFactor(riskFactor)
              : "Явный фактор риска не выявлен"}
          </div>
          <p className={styles.riskReasonText}>
            {hasActionableRiskFactor
              ? "Этот фактор сильнее всего связан с текущей вероятностью ухода клиента."
              : "Повышенное внимание требуется из-за общей вероятности ухода клиента."}
          </p>
        </div>
      </section>

      <section className={styles.healthSection}>
        <h3 className={styles.healthSectionTitle}>
          <Target size={15} />
          Рекомендуемое действие
        </h3>

        <div className={styles.nextActionBox}>
          <div className={styles.nextActionTitle}>
            {translateRecommendation(nextAction.recommendation_type)}
          </div>

          <p className={styles.nextActionText}>
            {nextAction.recommendation_reason
              ? translateRecommendationReason(nextAction.recommendation_reason)
              : "Для клиента не требуется отдельное действие по удержанию."}
          </p>

          <div className={styles.nextActionMeta}>
            <span>
              Приоритет:{" "}
              <strong>{translatePriority(nextAction.priority)}</strong>
            </span>
            <span>
              Под риском: <strong>{formatMoney(health.revenue_at_risk)}</strong>
            </span>
          </div>
        </div>
      </section>
    </aside>
  );
}

type CustomersPageProps = {
  initialFilters?: CustomerPageFilters;
};

export function CustomersPage({
  initialFilters = {},
}: CustomersPageProps) {
  const [customers, setCustomers] = useState<CustomerListItem[]>([]);
  const [totalCustomers, setTotalCustomers] = useState(0);

  const [filterOptions, setFilterOptions] = useState<CustomerFilterOptions>({
    risk_groups: [],
    segments: [],
    recommendations: [],
    main_risk_factors: [],
  });

  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(
    null
  );

  const [selectedCustomer, setSelectedCustomer] =
    useState<CustomerDetail | null>(null);

  const [search, setSearch] = useState(initialFilters.search ?? "");
  const [riskGroup, setRiskGroup] = useState(
    initialFilters.riskGroup ?? "All"
  );
  const [segment, setSegment] = useState(initialFilters.segment ?? "All");
  const [recommendation, setRecommendation] = useState(
    initialFilters.recommendation ?? "All"
  );
  const [mainRiskFactor, setMainRiskFactor] = useState(
    initialFilters.mainRiskFactor ?? "All"
  );
  const [minProbability, setMinProbability] = useState(
    initialFilters.minProbability ?? 0
  );

  const [isLoadingList, setIsLoadingList] = useState(true);
  const [error, setError] = useState("");

  const riskGroupOptions = filterOptions.risk_groups ?? [];
  const segmentOptions = filterOptions.segments ?? [];
  const recommendationOptions = filterOptions.recommendations ?? [];
  const mainRiskFactorOptions = filterOptions.main_risk_factors ?? [];

  useEffect(() => {
    fetchCustomerFilterOptions()
      .then((response: CustomerFilterOptions) => {
        setFilterOptions({
          risk_groups: response.risk_groups ?? [],
          segments: response.segments ?? [],
          recommendations: response.recommendations ?? [],
          main_risk_factors: response.main_risk_factors ?? [],
        });
      })
      .catch((error: Error) => {
        console.error(error);

        setFilterOptions({
          risk_groups: [],
          segments: [],
          recommendations: [],
          main_risk_factors: [],
        });
      });
  }, []);

  useEffect(() => {
    setIsLoadingList(true);
    setError("");

    fetchCustomers({
      search,
      riskGroup,
      segment,
      recommendation,
      mainRiskFactor,
      minProbability,
    })
      .then((response) => {
        const items = response.items ?? [];

        setCustomers(items);
        setTotalCustomers(response.total ?? items.length);

        if (items.length > 0) {
          setSelectedCustomerId(items[0].customer_id);
        } else {
          setSelectedCustomerId(null);
          setSelectedCustomer(null);
        }
      })
      .catch((error: Error) => {
        setCustomers([]);
        setTotalCustomers(0);
        setSelectedCustomerId(null);
        setSelectedCustomer(null);
        setError(error.message);
      })
      .finally(() => {
        setIsLoadingList(false);
      });
  }, [
    search,
    riskGroup,
    segment,
    recommendation,
    mainRiskFactor,
    minProbability,
  ]);

  useEffect(() => {
    if (!selectedCustomerId) {
      return;
    }

    fetchCustomerDetail(selectedCustomerId)
      .then((customer: CustomerDetail) => {
        setSelectedCustomer(customer);
      })
      .catch((error: Error) => {
        console.error(error);
        setSelectedCustomer(null);
      });
  }, [selectedCustomerId]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Клиенты</h1>
          <p className={styles.pageSubtitle}>
            Анализ скоринговых клиентов, риска оттока, сегментов и рекомендаций.
          </p>
        </div>

        <button
          type="button"
          className={styles.primaryButton}
          onClick={() =>
            downloadFilteredCustomers({
              search,
              riskGroup,
              segment,
              recommendation,
              mainRiskFactor,
              minProbability,
            })
          }
        >
          <Download size={17} />
          Выгрузить текущую выборку
        </button>
      </header>

      <section className={styles.filtersCard}>
        <div className={styles.filtersTitle}>
          <SlidersHorizontal size={16} />
          Фильтры
        </div>

        <div className={styles.filtersGrid}>
          <label className={styles.field}>
            Поиск по ID клиента
            <div className={styles.searchBox}>
              <Search size={16} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="C00001"
              />
            </div>
          </label>

          <label className={styles.field}>
            Группа риска
            <CustomSelect
              value={riskGroup}
              onChange={setRiskGroup}
              options={[
                { value: "All", label: "Все" },
                ...riskGroupOptions.map((item) => ({
                  value: item,
                  label: translateRiskGroup(item),
                })),
              ]}
            />
          </label>

          <label className={styles.field}>
            Сегмент
            <CustomSelect
              value={segment}
              onChange={setSegment}
              options={[
                { value: "All", label: "Все" },
                ...segmentOptions.map((item) => ({
                  value: item,
                  label: translateSegment(item),
                })),
              ]}
            />
          </label>

          <label className={styles.field}>
            Рекомендация
            <CustomSelect
              value={recommendation}
              onChange={setRecommendation}
              options={[
                { value: "All", label: "Все" },
                ...recommendationOptions.map((item) => ({
                  value: item,
                  label: translateRecommendation(item),
                })),
              ]}
            />
          </label>

          <label className={styles.field}>
            Фактор риска
            <CustomSelect
              value={mainRiskFactor}
              onChange={setMainRiskFactor}
              options={[
                { value: "All", label: "Все" },
                ...mainRiskFactorOptions.map((item) => ({
                  value: item,
                  label: translateRiskFactor(item),
                })),
              ]}
            />
          </label>

          <label className={styles.field}>
            Мин. вероятность оттока: {minProbability.toFixed(2)}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={minProbability}
              onChange={(event) =>
                setMinProbability(Number(event.target.value))
              }
            />
          </label>
        </div>
      </section>

      {error && (
        <div className={styles.errorBox}>
          Не удалось загрузить клиентов: {error}
        </div>
      )}

      <section className={styles.contentGrid}>
        <section className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <div>
              <h2>Список клиентов</h2>
              <p>
                {isLoadingList
                  ? "Загрузка клиентов..."
                  : `Показано клиентов: ${customers.length} из ${totalCustomers}`}
              </p>
            </div>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID клиента</th>
                  <th>Вероятность оттока</th>
                  <th>Группа риска</th>
                  <th>Сегмент</th>
                  <th>Оценочные расходы</th>
                  <th>Рекомендация</th>
                </tr>
              </thead>

              <tbody>
                {customers.map((customer) => {
                  const isSelected =
                    customer.customer_id === selectedCustomerId;

                  return (
                    <tr
                      key={customer.customer_id}
                      className={isSelected ? styles.selectedRow : ""}
                      onClick={() =>
                        setSelectedCustomerId(customer.customer_id)
                      }
                    >
                      <td className={styles.customerIdCell}>
                        <UserRound size={15} />
                        {customer.customer_id}
                      </td>

                      <td>{customer.churn_probability.toFixed(2)}</td>

                      <td>
                        <Badge tone={getRiskTone(customer.risk_group)}>
                          {translateRiskGroup(customer.risk_group)}
                        </Badge>
                      </td>

                      <td>{translateSegment(customer.segment_name)}</td>

                      <td>
                        {formatMoney(customer.estimated_total_charge)}
                      </td>

                      <td>
                        {translateRecommendation(
                          customer.recommendation_type
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {!isLoadingList && customers.length === 0 && (
              <div className={styles.emptyState}>
                Клиенты по выбранным фильтрам не найдены.
              </div>
            )}
          </div>
        </section>

        <CustomerDetailsPanel customer={selectedCustomer} />
      </section>
    </div>
  );
}
