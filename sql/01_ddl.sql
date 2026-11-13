-- UMFDOP Agent 3 - 01_ddl.sql - ZiG returns database (brief 2026-11-13)
-- Run: psql -d umfdop -v ON_ERROR_STOP=1 -f sql/01_ddl.sql      (PostgreSQL 18; builds from an empty database)
-- Tested in sandbox (PostgreSQL 18.7).

-- ===== 00 setup =====
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS audit;

-- ===== 01 conformed dimensions =====
CREATE TABLE core.dim_currency (
    currency_code char(3) PRIMARY KEY CHECK (currency_code ~ '^[A-Z]{3}$'),
    currency_name text NOT NULL
);
INSERT INTO core.dim_currency VALUES
    ('USD', 'US dollar'),
    ('ZWG', 'Zimbabwe Gold (ZiG), from April 2024'),
    ('ZWL', 'Zimbabwe dollar, before April 2024');

CREATE TABLE core.dim_source (
    source_id   varchar(10) PRIMARY KEY,
    publisher   text NOT NULL,
    title       text,
    url         text,
    as_of       date,
    reliability text NOT NULL CHECK (reliability IN ('primary', 'secondary'))
);
INSERT INTO core.dim_source VALUES
    ('D1', 'Reserve Bank of Zimbabwe', 'Daily interbank exchange rates (PDF per day)', 'https://www.rbz.co.zw/index.php/research/markets/exchange-rates', '2026-11-13', 'primary'),
    ('D2', 'International Monetary Fund', 'Exchange Rates (ER) dataset, Zimbabwe, monthly', 'https://data.imf.org/en/datasets/IMF.STA:ER', '2026-11-13', 'primary'),
    ('D3', 'Reserve Bank of Zimbabwe', 'Table 8.2 Average commercial banks deposit rates', 'https://www.rbz.co.zw/index.php/research/markets/interest-rates', '2026-11-13', 'primary'),
    ('D4', 'ZIMSTAT', 'Consumer Price Index releases (ZWG, USD, Weighted)', 'https://www.zimstat.co.zw/consumer-price-index/', '2026-11-13', 'primary'),
    ('D5', 'Federal Reserve Bank of St. Louis (FRED)', 'DTB3, SOFR, CPIAUCSL', 'https://fred.stlouisfed.org', '2026-11-13', 'primary'),
    ('D6', 'UMFDOP Agent 1', 'RBZ instrument and policy events (row status in fact table)', 'umfdop/briefs/agent1-brief-2026-11-13-zig-returns.md', '2026-11-13', 'secondary'),
    ('D7', 'First Capital Bank Zimbabwe', 'Daily rate sheet (republished RBZ interbank rate)', 'https://www.firstcapitalbank.co.zw/forex-reports', '2026-11-13', 'secondary');

CREATE TABLE core.dim_date (
    date_key     date PRIMARY KEY,
    year         smallint NOT NULL,
    quarter      smallint NOT NULL,
    month        smallint NOT NULL,
    month_name   text NOT NULL,
    is_month_end boolean NOT NULL,
    is_weekday   boolean NOT NULL
);
INSERT INTO core.dim_date
SELECT d::date,
       extract(year FROM d), extract(quarter FROM d), extract(month FROM d),
       to_char(d, 'Mon'),
       (d + interval '1 day')::date = date_trunc('month', d + interval '1 day')::date,
       extract(isodow FROM d) < 6
FROM generate_series('2015-01-01'::date, '2030-12-31'::date, interval '1 day') AS d;

CREATE TABLE core.dim_price_index (
    index_code    text PRIMARY KEY,
    index_name    text NOT NULL,
    currency_code char(3) REFERENCES core.dim_currency,   -- NULL for the weighted (ZWG + USD) index
    base_period   char(7) NOT NULL,
    source_id     varchar(10) NOT NULL REFERENCES core.dim_source
);
INSERT INTO core.dim_price_index VALUES
    ('ZWG',      'ZIMSTAT ZWG Consumer Price Index',                 'ZWG', '2024-04', 'D4'),
    ('USD',      'ZIMSTAT USD Consumer Price Index',                 'USD', '2022-06', 'D4'),
    ('Weighted', 'ZIMSTAT Weighted Consumer Price Index (ZWG + USD)', NULL, '2024-04', 'D4');

CREATE TABLE core.dim_series (
    series_id     text PRIMARY KEY,
    series_name   text NOT NULL,
    unit          text NOT NULL,
    frequency     text NOT NULL CHECK (frequency IN ('daily', 'monthly')),
    currency_code char(3) NOT NULL REFERENCES core.dim_currency,
    source_id     varchar(10) NOT NULL REFERENCES core.dim_source
);
INSERT INTO core.dim_series VALUES
    ('DTB3',     'US 3-month Treasury bill, secondary market', 'percent_pa_discount_basis', 'daily',   'USD', 'D5'),
    ('SOFR',     'Secured Overnight Financing Rate',           'percent_pa',                'daily',   'USD', 'D5'),
    ('CPIAUCSL', 'US CPI, all urban consumers, SA',            'index_1982_84=100',         'monthly', 'USD', 'D5');

-- ===== 02 temporal reference table: ZiG per USD (PostgreSQL 18 WITHOUT OVERLAPS) =====
-- One row per published rate; valid_at runs from the rate date to the next published rate date,
-- so weekends and holidays carry the last published rate.
CREATE TABLE core.fx_rate (
    currency_code         char(3)       NOT NULL REFERENCES core.dim_currency,
    rate_type             text          NOT NULL DEFAULT 'RBZ official',
    valid_at              daterange     NOT NULL,
    units_per_usd         numeric(18,6) NOT NULL CHECK (units_per_usd > 0),   -- mid
    bid_units_per_usd     numeric(18,6) CHECK (bid_units_per_usd > 0),
    ask_units_per_usd     numeric(18,6) CHECK (ask_units_per_usd > 0),
    pct_change_mid_pct    numeric(12,6),
    flag_jump_gt_5pct     boolean       NOT NULL,
    rate_source           text          NOT NULL CHECK (rate_source IN ('RBZ_interbank', 'FCB_republished_RBZ_interbank')),
    source_id             varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file           text          NOT NULL,
    loaded_at             timestamptz   NOT NULL,
    is_deleted            boolean       NOT NULL DEFAULT false,
    PRIMARY KEY (currency_code, rate_type, valid_at WITHOUT OVERLAPS),
    CHECK (bid_units_per_usd IS NULL OR ask_units_per_usd IS NULL
           OR (bid_units_per_usd < units_per_usd AND units_per_usd < ask_units_per_usd)),
    CHECK ((rate_source = 'RBZ_interbank') = (bid_units_per_usd IS NOT NULL))
);
CREATE INDEX ix_fx_rate_source ON core.fx_rate (source_id);
CREATE INDEX ix_fx_rate_lower ON core.fx_rate (lower(valid_at));

-- ===== 03 facts =====
-- Grain: one IMF exchange-rate observation per month per transformation.
CREATE TABLE core.fact_fx_imf_monthly (
    fact_id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_start           date          NOT NULL REFERENCES core.dim_date,
    period_end             date          NOT NULL REFERENCES core.dim_date,
    transformation         text          NOT NULL CHECK (transformation IN ('period_average', 'end_of_period')),
    currency_code          char(3)       NOT NULL REFERENCES core.dim_currency,
    usd_per_unit           numeric(28,16) NOT NULL CHECK (usd_per_unit > 0),
    local_per_usd          numeric(18,6) NOT NULL CHECK (local_per_usd > 0),
    flag_partial_zig_month boolean       NOT NULL,
    source_id              varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file            text          NOT NULL,
    loaded_at              timestamptz   NOT NULL,
    is_deleted             boolean       NOT NULL DEFAULT false,
    UNIQUE (period_start, transformation),
    CHECK (period_end = (period_start + interval '1 month - 1 day')::date)
);
CREATE INDEX ix_imf_period ON core.fact_fx_imf_monthly (period_start);
CREATE INDEX ix_imf_currency ON core.fact_fx_imf_monthly (currency_code);
CREATE INDEX ix_imf_source ON core.fact_fx_imf_monthly (source_id);

-- Grain: one month of quoted commercial-bank deposit rates (range of quotes, % p.a.) in one currency.
CREATE TABLE core.fact_deposit_rate_monthly (
    fact_id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_start             date         NOT NULL REFERENCES core.dim_date,
    period_end               date         NOT NULL REFERENCES core.dim_date,
    currency_code            char(3)      NOT NULL REFERENCES core.dim_currency,
    savings_min_pct          numeric(9,6) NOT NULL CHECK (savings_min_pct BETWEEN 0 AND 1000),
    savings_max_pct          numeric(9,6) NOT NULL CHECK (savings_max_pct BETWEEN 0 AND 1000),
    three_month_min_pct      numeric(9,6) NOT NULL CHECK (three_month_min_pct BETWEEN 0 AND 1000),
    three_month_max_pct      numeric(9,6) NOT NULL CHECK (three_month_max_pct BETWEEN 0 AND 1000),
    flag_savings_min_gt_max  boolean      NOT NULL,
    flag_3m_min_gt_max       boolean      NOT NULL,
    flag_same_as_prior_month boolean      NOT NULL,
    source_id                varchar(10)  NOT NULL REFERENCES core.dim_source,
    source_file              text         NOT NULL,
    loaded_at                timestamptz  NOT NULL,
    is_deleted               boolean      NOT NULL DEFAULT false,
    UNIQUE (period_start, currency_code),
    CHECK ((currency_code = 'ZWG') = (period_start >= DATE '2024-04-01')),  -- ZiG rows only from April 2024
    CHECK (flag_savings_min_gt_max = (savings_min_pct > savings_max_pct)),
    CHECK (flag_3m_min_gt_max = (three_month_min_pct > three_month_max_pct))
);
CREATE INDEX ix_dep_period ON core.fact_deposit_rate_monthly (period_start);
CREATE INDEX ix_dep_currency ON core.fact_deposit_rate_monthly (currency_code);
CREATE INDEX ix_dep_source ON core.fact_deposit_rate_monthly (source_id);

-- Grain: one CPI level per index per month (gaps filled per Agent 2 rule R11; imputed rows flagged).
CREATE TABLE core.fact_cpi_monthly (
    fact_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    index_code   text          NOT NULL REFERENCES core.dim_price_index,
    period_start date          NOT NULL REFERENCES core.dim_date,
    period_end   date          NOT NULL REFERENCES core.dim_date,
    index_base   text          NOT NULL CHECK (index_base IN ('2024-04=100', '2022-06=100')),
    index_level  numeric(12,2) NOT NULL CHECK (index_level > 0),
    mom_pct      numeric(12,6),
    yoy_pct      numeric(12,6),
    fill_method  text          NOT NULL CHECK (fill_method IN ('reported_own_release', 'reported_in_next_release',
                                                               'reported_in_release_12m_later', 'base_period_definition',
                                                               'chained_from_mom_1dp')),
    is_imputed   boolean       NOT NULL,
    source_id    varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file  text          NOT NULL,
    loaded_at    timestamptz   NOT NULL,
    is_deleted   boolean       NOT NULL DEFAULT false,
    UNIQUE (index_code, period_start),
    CHECK (is_imputed = (fill_method = 'chained_from_mom_1dp'))
);
CREATE INDEX ix_cpi_period ON core.fact_cpi_monthly (period_start);
CREATE INDEX ix_cpi_index ON core.fact_cpi_monthly (index_code);
CREATE INDEX ix_cpi_source ON core.fact_cpi_monthly (source_id);

-- Grain: one CPI level as stated in one ZIMSTAT release (evidence trail behind fact_cpi_monthly).
CREATE TABLE core.fact_cpi_observation (
    fact_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    index_code    text          NOT NULL REFERENCES core.dim_price_index,
    period_start  date          NOT NULL REFERENCES core.dim_date,
    published_in  date          NOT NULL REFERENCES core.dim_date,
    role          text          NOT NULL CHECK (role IN ('current', 'prior_month', 'prior_year')),
    index_level   numeric(12,2) NOT NULL CHECK (index_level > 0),
    index_base    text,
    source_id     varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file   text          NOT NULL,
    loaded_at     timestamptz   NOT NULL,
    is_deleted    boolean       NOT NULL DEFAULT false,
    UNIQUE (index_code, period_start, published_in, role)
);
CREATE INDEX ix_cpiobs_period ON core.fact_cpi_observation (period_start);
CREATE INDEX ix_cpiobs_index ON core.fact_cpi_observation (index_code);
CREATE INDEX ix_cpiobs_pub ON core.fact_cpi_observation (published_in);
CREATE INDEX ix_cpiobs_source ON core.fact_cpi_observation (source_id);

-- Grain: one observation per US benchmark series per date.
CREATE TABLE core.fact_us_benchmark (
    fact_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id     text          NOT NULL REFERENCES core.dim_series,
    obs_date      date          NOT NULL REFERENCES core.dim_date,
    value         numeric(14,6) NOT NULL,
    currency_code char(3)       NOT NULL REFERENCES core.dim_currency,
    source_id     varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file   text          NOT NULL,
    loaded_at     timestamptz   NOT NULL,
    is_deleted    boolean       NOT NULL DEFAULT false,
    UNIQUE (series_id, obs_date)
);
CREATE INDEX ix_us_date ON core.fact_us_benchmark (obs_date);
CREATE INDEX ix_us_series ON core.fact_us_benchmark (series_id);
CREATE INDEX ix_us_currency ON core.fact_us_benchmark (currency_code);
CREATE INDEX ix_us_source ON core.fact_us_benchmark (source_id);

-- Grain: one RBZ instrument or policy event.
CREATE TABLE core.fact_rbz_event (
    fact_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_date    date          NOT NULL REFERENCES core.dim_date,
    event_type    text          NOT NULL CHECK (event_type IN ('launch', 'devaluation', 'min_deposit_rate', 'zigdtdf_auction',
                                                               'zigdtdf_tap', 'policy_rate')),
    instrument    text          NOT NULL,
    tenor_days    integer       CHECK (tenor_days > 0),
    currency_code char(3)       NOT NULL REFERENCES core.dim_currency,
    rate_pct      numeric(9,4)  CHECK (rate_pct BETWEEN 0 AND 1000),
    amount_zwg_m  numeric(18,2) CHECK (amount_zwg_m >= 0),
    source_url    text          NOT NULL,
    status        text          NOT NULL CHECK (status IN ('verified', 'single_source', 'unverified')),
    source_id     varchar(10)   NOT NULL REFERENCES core.dim_source,
    source_file   text          NOT NULL,
    loaded_at     timestamptz   NOT NULL,
    is_deleted    boolean       NOT NULL DEFAULT false,
    UNIQUE NULLS NOT DISTINCT (event_date, event_type, instrument, tenor_days, currency_code)
);
CREATE INDEX ix_event_date ON core.fact_rbz_event (event_date);
CREATE INDEX ix_event_currency ON core.fact_rbz_event (currency_code);
CREATE INDEX ix_event_source ON core.fact_rbz_event (source_id);

-- ===== 04 staging: mirrors Agent 2's clean files column for column =====
CREATE TABLE stg.fx_usd_zwg_daily (rate_date date, base_currency text, quote_currency text, bid numeric, ask numeric,
    mid numeric, pct_change_mid numeric, flag_jump_gt_5pct boolean, rate_source text, source_id text, source_file text, loaded_at timestamptz);
CREATE TABLE stg.fx_imf_monthly (period text, period_start date, period_end date, transformation text, currency text,
    usd_per_unit numeric, local_per_usd numeric, flag_partial_zig_month boolean, source_id text, source_file text, loaded_at timestamptz);
CREATE TABLE stg.deposit_rates_monthly (period text, period_start date, period_end date, currency text,
    savings_min_pct numeric, savings_max_pct numeric, three_month_min_pct numeric, three_month_max_pct numeric,
    flag_savings_min_gt_max boolean, flag_3m_min_gt_max boolean, flag_same_as_prior_month boolean,
    source_id text, source_file text, loaded_at timestamptz);
CREATE TABLE stg.cpi_observations (cpi_type text, period text, index_level numeric, role text, published_in text,
    index_base text, source_file text, source_id text, loaded_at timestamptz);
CREATE TABLE stg.cpi_monthly (cpi_type text, period text, period_start date, period_end date, index_base text,
    index_level numeric, mom_pct numeric, yoy_pct numeric, fill_method text, is_imputed boolean,
    source_id text, source_file text, loaded_at timestamptz);
CREATE TABLE stg.us_benchmarks (series_id text, obs_date date, value numeric, unit text, frequency text, currency text,
    source_id text, source_file text, loaded_at timestamptz);
CREATE TABLE stg.rbz_events (event_date date, event_type text, instrument text, tenor_days numeric, currency text,
    rate_pct numeric, amount_zwg_m numeric, source_url text, status text, source_file text, source_id text, loaded_at timestamptz);

-- ===== 05 audit =====
CREATE TABLE audit.load_log (
    load_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_table  text NOT NULL,
    file_name     text NOT NULL,
    rows_agent2   integer NOT NULL,
    rows_staged   integer NOT NULL,
    rows_promoted integer NOT NULL,
    loaded_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== 06 mart views (Agent 4 and BI read only these) =====
-- One ZiG/USD rate per calendar day; weekends and holidays carry the last published rate.
CREATE VIEW mart.v_fx_daily AS
SELECT d.date_key, r.currency_code, r.rate_type,
       r.units_per_usd, r.bid_units_per_usd, r.ask_units_per_usd,
       lower(r.valid_at)                 AS rate_observed_on,
       d.date_key <> lower(r.valid_at)   AS is_carried_forward,
       d.is_weekday,
       r.flag_jump_gt_5pct AND d.date_key = lower(r.valid_at) AS flag_jump_gt_5pct,
       r.rate_source, r.source_id
FROM core.fx_rate r
JOIN core.dim_date d ON r.valid_at @> d.date_key
WHERE NOT r.is_deleted;

-- Month-level ZiG/USD: average of published days, rate in force on the last calendar day, and IMF comparators.
CREATE VIEW mart.v_fx_monthly AS
WITH m AS (
    SELECT date_trunc('month', date_key)::date AS period_start,
           avg(units_per_usd) FILTER (WHERE NOT is_carried_forward) AS avg_units_per_usd,
           count(*) FILTER (WHERE NOT is_carried_forward)            AS published_days,
           max(date_key)                                             AS last_day_in_data
    FROM mart.v_fx_daily GROUP BY 1
)
SELECT m.period_start, to_char(m.period_start, 'YYYY-MM') AS period, 'ZWG'::char(3) AS currency_code,
       round(m.avg_units_per_usd, 6) AS avg_units_per_usd,
       e.units_per_usd AS eop_units_per_usd,
       (m.last_day_in_data = (m.period_start + interval '1 month - 1 day')::date) AS is_complete_month,
       m.published_days,
       ia.local_per_usd AS imf_avg_units_per_usd,
       ie.local_per_usd AS imf_eop_units_per_usd
FROM m
JOIN mart.v_fx_daily e ON e.date_key = m.last_day_in_data
LEFT JOIN core.fact_fx_imf_monthly ia ON ia.period_start = m.period_start AND ia.transformation = 'period_average' AND NOT ia.is_deleted
LEFT JOIN core.fact_fx_imf_monthly ie ON ie.period_start = m.period_start AND ie.transformation = 'end_of_period' AND NOT ie.is_deleted;

CREATE VIEW mart.v_cpi_monthly AS
SELECT c.period_start, to_char(c.period_start, 'YYYY-MM') AS period, c.index_code, p.currency_code, c.index_base,
       c.index_level, c.mom_pct, c.yoy_pct, c.fill_method, c.is_imputed, c.source_id
FROM core.fact_cpi_monthly c JOIN core.dim_price_index p USING (index_code)
WHERE NOT c.is_deleted;

CREATE VIEW mart.v_deposit_rates_monthly AS
SELECT period_start, to_char(period_start, 'YYYY-MM') AS period, currency_code,
       savings_min_pct, savings_max_pct, three_month_min_pct, three_month_max_pct,
       flag_savings_min_gt_max, flag_3m_min_gt_max, flag_same_as_prior_month, source_id
FROM core.fact_deposit_rate_monthly WHERE NOT is_deleted;

CREATE VIEW mart.v_us_benchmarks_monthly AS
SELECT date_trunc('month', b.obs_date)::date AS period_start, to_char(date_trunc('month', b.obs_date), 'YYYY-MM') AS period,
       b.series_id, s.unit, s.currency_code,
       round(avg(b.value), 6) AS avg_value,
       (array_agg(b.value ORDER BY b.obs_date DESC))[1] AS last_value,
       count(*) AS observations
FROM core.fact_us_benchmark b JOIN core.dim_series s USING (series_id)
WHERE NOT b.is_deleted
GROUP BY 1, 2, 3, 4, 5;

CREATE VIEW mart.v_rbz_events AS
SELECT event_date, event_type, instrument, tenor_days, currency_code, rate_pct, amount_zwg_m, status, source_url
FROM core.fact_rbz_event WHERE NOT is_deleted;

-- One row per month with every input Agent 4 needs for BQ1-BQ2 (no return calculations here).
CREATE VIEW mart.v_monthly_inputs AS
SELECT d.period_start, to_char(d.period_start, 'YYYY-MM') AS period,
       fx.eop_units_per_usd   AS zwg_per_usd_eop,
       fx.avg_units_per_usd   AS zwg_per_usd_avg,
       fx.is_complete_month   AS fx_complete_month,
       zc.index_level AS zwg_cpi,      zc.is_imputed AS zwg_cpi_imputed,
       uc.index_level AS zim_usd_cpi,  uc.is_imputed AS zim_usd_cpi_imputed,
       wc.index_level AS weighted_cpi, wc.is_imputed AS weighted_cpi_imputed,
       dr.savings_min_pct, dr.savings_max_pct, dr.three_month_min_pct, dr.three_month_max_pct,
       dr.flag_savings_min_gt_max,
       tb.avg_value AS us_tbill_3m_discount_pct_avg,
       sf.avg_value AS sofr_pct_avg,
       uscpi.last_value AS us_cpi
FROM (SELECT DISTINCT date_trunc('month', date_key)::date AS period_start FROM mart.v_fx_daily) d
LEFT JOIN mart.v_fx_monthly fx ON fx.period_start = d.period_start
LEFT JOIN mart.v_cpi_monthly zc ON zc.period_start = d.period_start AND zc.index_code = 'ZWG'
LEFT JOIN mart.v_cpi_monthly uc ON uc.period_start = d.period_start AND uc.index_code = 'USD'
LEFT JOIN mart.v_cpi_monthly wc ON wc.period_start = d.period_start AND wc.index_code = 'Weighted'
LEFT JOIN mart.v_deposit_rates_monthly dr ON dr.period_start = d.period_start AND dr.currency_code = 'ZWG'
LEFT JOIN mart.v_us_benchmarks_monthly tb ON tb.period_start = d.period_start AND tb.series_id = 'DTB3'
LEFT JOIN mart.v_us_benchmarks_monthly sf ON sf.period_start = d.period_start AND sf.series_id = 'SOFR'
LEFT JOIN mart.v_us_benchmarks_monthly uscpi ON uscpi.period_start = d.period_start AND uscpi.series_id = 'CPIAUCSL';

-- ===== 07 read-only role for Power BI and Tableau =====
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bi_reader') THEN CREATE ROLE bi_reader NOLOGIN; END IF;
END $$;
GRANT USAGE ON SCHEMA mart TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO bi_reader;
