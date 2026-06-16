# Churn Analytics

Система анализа оттока клиентов:

- FastAPI предоставляет Dashboard, клиентов, сегменты, рекомендации и экспорт;
- React поддерживает аналитику и drill-down к отфильтрованным клиентам;
- ML-пайплайн обучает Gradient Boosting и регистрирует модель в MLflow;
- Airflow запускает канонический пайплайн из `ml_service`;
- PostgreSQL хранит исходные данные и результаты скоринга.

## ML-логика

- `train` используется только для обучения;
- `validation` используется для промежуточной оценки;
- `test` используется для финальных метрик Dashboard;
- `scoring_batch` используется только для прогнозирования;
- сегментация является rule-based, а не кластеризацией;
- клиентам низкого риска назначается `No Action`.

Старые автономные скрипты удалены, чтобы бизнес-правила не расходились с
основным пайплайном.

## Инференс и пересчет клиентов

В проекте есть два ML-сценария:

- `run_weekly_pipeline` обучает новую модель, регистрирует ее в MLflow и
  пересчитывает витринные таблицы;
- `run_scoring_pipeline` не обучает модель, а берет последнюю
  зарегистрированную модель из MLflow и пересчитывает клиентов из
  `client_records_raw`, у которых `dataset_split = 'scoring_batch'`.

Новые или обновленные клиенты должны попадать в `client_records_raw` со
значением `dataset_split = 'scoring_batch'`. После запуска scoring pipeline
пересчитываются:

- `predictions`;
- `customer_segments`;
- `customer_recommendations`.

Структура БД при этом не меняется: pipeline заменяет содержимое витринных
таблиц актуальным результатом инференса.

Локальный запуск инференса:

```powershell
$env:CHURN_DATABASE_URL="postgresql+psycopg2://admin:1111@localhost:5432/churn_db"
$env:MLFLOW_TRACKING_URI="http://localhost:5000"
$env:MLFLOW_MODEL_URI="models:/churn_classifier/latest"
cd ml_service
python scripts/run_scoring_pipeline.py
```

Если `MLFLOW_MODEL_URI` не задан, pipeline использует
`models:/$env:MLFLOW_REGISTERED_MODEL_NAME/latest`.

Запуск через Docker Compose:

```powershell
docker compose run --rm ml-service python scripts/run_scoring_pipeline.py
```

В Airflow для ручного пересчета доступен DAG `churn_scoring_pipeline`.

## Демо-аугментация scoring-выборки

Для демонстрации продукта можно увеличить `scoring_batch` синтетическими
клиентами на основе уже существующих scoring-записей. Скрипт не меняет
структуру БД: он добавляет новые строки в `client_records_raw` с
`customer_id` вида `SYN_00001`.

```powershell
$env:CHURN_DATABASE_URL="postgresql+psycopg2://admin:1111@localhost:5432/churn_db"
cd ml_service
python scripts/augment_scoring_customers.py --target-count 1800
python scripts/run_scoring_pipeline.py
```

После этого интерфейс будет показывать пересчитанную витрину по расширенной
scoring-выборке.

## Установка

```powershell
python -m pip install -r requirements.txt
cd frontend
npm install
```

Backend использует `DATABASE_URL`, ML-пайплайн использует
`CHURN_DATABASE_URL`. Значения задаются в `.env`.

## Запуск

```powershell
cd backend
uvicorn app.main:app --reload
cd frontend
npm run dev
```

Инфраструктурные сервисы запускаются через `docker compose up`.
