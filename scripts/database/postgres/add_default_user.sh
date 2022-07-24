#!/bin/bash
set -e

# insert a default user
# - email: user@example.com
# - password: 123456
# N.B. password is crypted by the API_JWT_TOKEN_SECRET. Please DO NOT change the value of API_JWT_TOKEN_SECRET
PGPASSWORD=postgres psql -v ON_ERROR_STOP=1 -h localhost -U postgres -d nm <<-EOSQL
    INSERT INTO users(id, full_name, is_active, is_superuser, email, hashed_password, login_type, ext_info, created_at, updated_at)
    VALUES (138838033, 'Awesome User', true, false, 'user@example.com', '\$2b\$12\$7dznv/XSi7lQVvGOouPgXuuvnCl2HGSjyx1ibJJj7l9NGyh8qaPby', 'email', NULL, current_timestamp, current_timestamp);
EOSQL
