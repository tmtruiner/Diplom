import { useEffect, useState } from "react";
import { X, BrainCircuit } from "lucide-react";

import { fetchDashboardSummary } from "../../services/dashboardApi";
import type { DashboardSummary } from "../../types/dashboard";
import { formatDateTime } from "../../utils/formatDate";
import styles from "./ModelInfoModal.module.css";

type ModelInfoModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function ModelInfoModal({ isOpen, onClose }: ModelInfoModalProps) {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!isOpen || data) {
      return;
    }

    setIsLoading(true);
    setErrorMessage("");

    fetchDashboardSummary()
      .then(setData)
      .catch((error) => {
        setErrorMessage(error.message);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isOpen, data]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  const scoringInfo = data?.scoring_info;

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <section
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="model-info-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className={styles.header}>
          <div className={styles.titleBlock}>
            <div className={styles.iconBox}>
              <BrainCircuit size={22} />
            </div>

            <div>
              <h2 id="model-info-title" className={styles.title}>
                Информация о модели
              </h2>
              <p className={styles.subtitle}>
                Технические сведения о текущей модели скоринга оттока.
              </p>
            </div>
          </div>

          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Закрыть окно"
          >
            <X size={18} />
          </button>
        </header>

        {isLoading && (
          <div className={styles.skeletonGrid}>
            {Array.from({ length: 7 }).map((_, index) => (
              <div key={index} className={styles.skeletonItem} />
            ))}
          </div>
        )}

        {errorMessage && (
          <div className={styles.errorBox}>
            Не удалось загрузить информацию о модели: {errorMessage}
          </div>
        )}

        {!isLoading && !errorMessage && scoringInfo && (
          <>
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Модель</h3>

              <div className={styles.grid}>
                <InfoItem
                  label="Название модели"
                  value={scoringInfo.model_name ?? "-"}
                />

                <InfoItem
                  label="Версия модели"
                  value={scoringInfo.model_version ?? "-"}
                />

                <InfoItem
                  label="Алгоритм"
                  value={scoringInfo.algorithm ?? "-"}
                />

                <InfoItem
                  label="Дата последнего скоринга"
                  value={formatDateTime(scoringInfo.last_scoring_date)}
                />
              </div>
            </div>

            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Метрики качества</h3>

              <div className={styles.grid}>
                <InfoItem
                  label="ROC-AUC"
                  value={scoringInfo.roc_auc?.toFixed(2) ?? "-"}
                />

                <InfoItem
                  label="F1-score"
                  value={scoringInfo.f1_score?.toFixed(2) ?? "-"}
                />

                <InfoItem
                  label="Recall"
                  value={scoringInfo.recall?.toFixed(2) ?? "-"}
                />
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.infoItem}>
      <div className={styles.infoLabel}>{label}</div>
      <div className={styles.infoValue}>{value}</div>
    </div>
  );
}