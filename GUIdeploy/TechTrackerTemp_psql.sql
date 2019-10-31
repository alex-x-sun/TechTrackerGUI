CREATE TABLE tech_main (
    id serial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    is_use boolean NOT NULL DEFAULT false,
    is_prod boolean NOT NULL DEFAULT false,
    is_proc boolean NOT NULL DEFAULT false,
    description text,
    impact text,
    impa_sector text,
    sources text

);


CREATE TABLE tech_lookup (
  lookup_id serial PRIMARY KEY,
  tech_main_id integer REFERENCES tech_main (id) not null,
  tech_lookup_name text NOT NULL unique);

CREATE TABLE tech_embed (
    id integer PRIMARY KEY REFERENCES tech_main(id),
    embed_li text,
    embed_main_techs text,
    embed_main_tech_ids text
);

CREATE TABLE tech_main_log (
  log_id serial PRIMARY KEY, -- SERIAL PRIMARY KEY (Postgres)
  contributor integer NOT NULL,
  tech_name text NOT NULL,
  scout_time timestamp without time zone NOT NULL,
  description text NOT NULL,
  desc_source text,
  impact text NOT NULL,
  impa_source text,
  impa_sector text,
  asso_names text,
  emb_techs text,
  edited boolean,
  wiki_link text,
  category text,
  change_committed timestamp without time zone
);

CREATE TABLE tech_story_log (
  log_s_id serial PRIMARY KEY,
  contributor integer NOT NULL,
  contribute_time timestamp without time zone NOT NULL,
  tech_name text NOT NULL,
  story_year integer NOT NULL,
  story_date text,
  story_content text NOT NULL,
  milestone text NOT NULL,
  sources text,
  change_committed timestamp without time zone
);

CREATE TABLE tech_story (
    story_id serial PRIMARY KEY,
    id integer REFERENCES tech_main(id) not null,
    name text NOT NULL,
    story_time timestamp without time zone NOT NULL,
    story_content text NOT NULL,
    milestone text,
    exact_time integer,
    source_check integer,
    sources text,
    story_year integer NOT NULL

);

CREATE TABLE users (
  user_id serial PRIMARY KEY, -- SERIAL PRIMARY KEY,
  username text unique,
  email text NOT NULL unique,
  password text NOT NULL,
  can_scout boolean DEFAULT True,
  can_analyse boolean DEFAULT True,
  can_edit boolean DEFAULT False,
  admin boolean DEFAULT False
);


-- CREATE TABLE impacted_sector_order (
--   sec_id integer PRIMARY KEY,
--   sector text
-- );
--
-- CREATE TABLE "milestones" (
--  "index" INTEGER,
--   "ma_std_name" TEXT,
--   "milestone_id" INTEGER,
--   "ms_name" TEXT
-- )

CREATE TABLE tech_wiki (
    tech_id integer REFERENCES tech_main(id),
    wiki_link text
);
