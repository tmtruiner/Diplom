BEGIN;

-- 1. Добавляем технический id в исходную таблицу клиентов
ALTER TABLE client_records_raw
ADD COLUMN IF NOT EXISTS id integer;

CREATE SEQUENCE IF NOT EXISTS client_records_raw_id_seq;

WITH numbered_rows AS (
    SELECT
        ctid,
        row_number() OVER (ORDER BY ctid) AS rn
    FROM client_records_raw
    WHERE id IS NULL
)
UPDATE client_records_raw AS c
SET id = numbered_rows.rn
FROM numbered_rows
WHERE c.ctid = numbered_rows.ctid;

SELECT setval(
    'client_records_raw_id_seq',
    COALESCE((SELECT MAX(id) FROM client_records_raw), 1),
    true
);

ALTER TABLE client_records_raw
ALTER COLUMN id SET DEFAULT nextval('client_records_raw_id_seq');

ALTER TABLE client_records_raw
ALTER COLUMN id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'client_records_raw_pkey'
    ) THEN
        ALTER TABLE client_records_raw
        ADD CONSTRAINT client_records_raw_pkey PRIMARY KEY (id);
    END IF;
END $$;


-- 2. Добавляем customer_id в исходную таблицу
ALTER TABLE client_records_raw
ADD COLUMN IF NOT EXISTS customer_id text;

UPDATE client_records_raw
SET customer_id = 'C' || LPAD(id::text, 5, '0')
WHERE customer_id IS NULL;

ALTER TABLE client_records_raw
ALTER COLUMN customer_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'client_records_raw_customer_id_unique'
    ) THEN
        ALTER TABLE client_records_raw
        ADD CONSTRAINT client_records_raw_customer_id_unique UNIQUE (customer_id);
    END IF;
END $$;


-- 3. Добавляем служебное поле для разделения датасета
ALTER TABLE client_records_raw
ADD COLUMN IF NOT EXISTS dataset_split text;

-- Вариант автоматического разделения:
-- 60% train, 15% validation, 15% test, 10% scoring_batch.
-- Если у тебя уже есть готовое разделение, этот UPDATE можно заменить своим.
WITH split_rows AS (
    SELECT
        id,
        row_number() OVER (ORDER BY id) AS rn,
        count(*) OVER () AS total_count
    FROM client_records_raw
)
UPDATE client_records_raw AS c
SET dataset_split =
    CASE
        WHEN split_rows.rn <= split_rows.total_count * 0.60 THEN 'train'
        WHEN split_rows.rn <= split_rows.total_count * 0.75 THEN 'validation'
        WHEN split_rows.rn <= split_rows.total_count * 0.90 THEN 'test'
        ELSE 'scoring_batch'
    END
FROM split_rows
WHERE c.id = split_rows.id
  AND c.dataset_split IS NULL;

ALTER TABLE client_records_raw
ALTER COLUMN dataset_split SET NOT NULL;


-- 4. Добавляем scoring_job_id в predictions
ALTER TABLE predictions
ADD COLUMN IF NOT EXISTS scoring_job_id integer;


-- 5. Делаем customer_id в predictions уникальным
-- Это нужно, чтобы customer_segments и customer_recommendations могли ссылаться на predictions(customer_id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'predictions_customer_id_unique'
    ) THEN
        ALTER TABLE predictions
        ADD CONSTRAINT predictions_customer_id_unique UNIQUE (customer_id);
    END IF;
END $$;


-- 6. Связь predictions -> client_records_raw
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_predictions_customer_raw'
    ) THEN
        ALTER TABLE predictions
        ADD CONSTRAINT fk_predictions_customer_raw
        FOREIGN KEY (customer_id)
        REFERENCES client_records_raw(customer_id)
        ON DELETE CASCADE;
    END IF;
END $$;


-- 7. Связь predictions -> scoring_jobs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_predictions_scoring_job'
    ) THEN
        ALTER TABLE predictions
        ADD CONSTRAINT fk_predictions_scoring_job
        FOREIGN KEY (scoring_job_id)
        REFERENCES scoring_jobs(id)
        ON DELETE SET NULL;
    END IF;
END $$;


-- 8. Связь customer_segments -> predictions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_customer_segments_prediction'
    ) THEN
        ALTER TABLE customer_segments
        ADD CONSTRAINT fk_customer_segments_prediction
        FOREIGN KEY (customer_id)
        REFERENCES predictions(customer_id)
        ON DELETE CASCADE;
    END IF;
END $$;


-- 9. Связь customer_recommendations -> predictions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_customer_recommendations_prediction'
    ) THEN
        ALTER TABLE customer_recommendations
        ADD CONSTRAINT fk_customer_recommendations_prediction
        FOREIGN KEY (customer_id)
        REFERENCES predictions(customer_id)
        ON DELETE CASCADE;
    END IF;
END $$;

COMMIT;