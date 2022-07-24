CREATE SEQUENCE IF NOT EXISTS seq_id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE OR REPLACE FUNCTION next_id() RETURNS bigint
    LANGUAGE sql
    AS $$
      SELECT ((FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000) /* now_millis */
                  - 1620488843862 /* our_epoch */)::bigint % 131072 /* 2^17, at most 17 bit */ ) << 14
            | (1 + 0 /* shard_id */ << 4)
            | (nextval('seq_id') % 1024 /* seq_id */);
$$;


