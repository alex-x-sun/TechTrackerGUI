CREATE TABLE tech_main (
    id integer PRIMARY KEY autoincrement,
    name text varying NOT NULL,
    is_use boolean NOT NULL DEFAULT false,
    is_prod boolean NOT NULL DEFAULT false,
    is_proc boolean NOT NULL DEFAULT false,
    description text,
    impact text
);

CREATE TABLE tech_lookup (
  lookup_id integer PRIMARY KEY autoincrement,
  tech_main_id NOT NULL REFERENCES tech_main(id),
  tech_lookup_name text NOT NULL
);

CREATE TABLE tech_main_log (
  log_id integer PRIMARY KEY autoincrement,
  contributor integer NOT NULL,
  tech_name text NOT NULL,
  scout_time timestamp without time zone NOT NULL,
  description text NOT NULL,
  desc_source text,
  impact text NOT NULL,
  impa_source text,
  impa_sector text,
  asso_names text,
  emb_techs text

);

CREATE TABLE impacted_sector_order (
  sec_id integer PRIMARY KEY,
  sector text
);
