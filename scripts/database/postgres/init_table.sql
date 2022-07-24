CREATE TABLE IF NOT EXISTS users (
    id bigint primary key DEFAULT next_id(),
    full_name varchar(200) not null,
    is_active boolean default true,
    is_superuser boolean default false,
    email varchar(200),
    hashed_password varchar(200),
    login_type varchar(20),
    ext_info json,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
);
-- CREATE TABLE IF NOT EXISTS tasks (
--     id serial primary key,
--     user_id integer,
--     is_public boolean default false,
--     nm_type varchar(200),
--     nm_name varchar(200),
--     nm_status varchar(200),
--     nm_desc varchar(200),
--     ext_info json,
--     created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
--     updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
-- );
CREATE TABLE IF NOT EXISTS groups (
    id bigint primary key DEFAULT next_id(),
    owner_id bigint references users(id),
    name varchar(200),
    description varchar(200),
    is_active boolean default true,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    ext_info text
);
CREATE TABLE IF NOT EXISTS group_members (
    id bigint primary key DEFAULT next_id(),
    group_id bigint references groups(id),
    member_id bigint references users(id)
);
CREATE TABLE IF NOT EXISTS medias (
    id bigint primary key DEFAULT next_id(),
    owner_id bigint references users(id),
    location varchar(200),
    content_type varchar(20),
    e_tag varchar(200),
    is_active boolean default true,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    ext_info text
);
CREATE TABLE IF NOT EXISTS datasets (
    id bigint primary key DEFAULT next_id(),
    owner_id bigint references users(id),
    name varchar(200),
    description varchar(200),
    media_id bigint references medias(id),
    is_active boolean default true,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
);
CREATE TABLE IF NOT EXISTS abcxyz_tasks (
    id bigint primary key DEFAULT next_id(),
    name varchar(200),
    description varchar(200),
    owner_id bigint references users(id),
    is_public boolean,
    is_active boolean default true,
    type text, -- TODO: what is the type of the column type?
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    ext_info text
);

-- create table abcxyz_tasks_users (
--     abcxyz_task_id references datasets(id),
--     user_id references users(id)
-- );

-- create table abcxyz_tasks_groups (
--     abcxyz_task_id references datasets(id),
--     group_id references groups(id)
-- );
CREATE TABLE IF NOT EXISTS dataset_shared_groups (
    id bigint primary key DEFAULT next_id(),
    dataset_id bigint references datasets(id),
    group_id bigint references groups(id)
);
CREATE TABLE IF NOT EXISTS dataset_shared_users (
    id bigint primary key DEFAULT next_id(),
    dataset_id bigint references datasets(id),
    user_id bigint references users(id)
);

CREATE TABLE IF NOT EXISTS oauth2_users (
    id bigint primary key DEFAULT next_id(),
    provider varchar(20),
    provider_id int,
    owner_id bigint references users(id),
    ext_info text,
    is_active boolean default true,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_codes (
    id bigint primary key DEFAULT next_id(),
    action varchar(30),
    email varchar(200),
    vcode varchar(30),
    is_active boolean default true,
    expire_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    updated_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS local_deploy_users (
    id bigint primary key DEFAULT next_id(),
    email varchar(200),
    user_id bigint references users(id),
    is_active boolean default false,
    company varchar(200),
    role varchar(200),
    purpose varchar(200),
    requested_at timestamp without time zone DEFAULT timezone('UTC'::text, now()) NOT NULL,
    approved_at timestamp without time zone,
    expire_at timestamp without time zone
);
