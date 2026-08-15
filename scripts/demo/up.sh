#!/bin/sh
set -eu

admin_username=${1:-}
if [ -z "$admin_username" ]; then
    printf 'Admin username: '
    read -r admin_username
fi

if [ -z "$admin_username" ]; then
    printf '%s\n' 'An admin username is required.' >&2
    exit 2
fi

docker compose up --build --detach --wait

set +e
docker compose exec --no-TTY -e "DEMO_ADMIN_USERNAME=$admin_username" app python -c '
import os
from sqlalchemy import select
from varys.auth import User
from varys.config import load_settings
from varys.db import create_session_factory

settings = load_settings()
with create_session_factory(settings.database_url)() as database:
    exists = database.scalar(
        select(User.id).where(User.username == os.environ["DEMO_ADMIN_USERNAME"])
    ) is not None
raise SystemExit(0 if exists else 1)
'
existing_user=$?
set -e

case "$existing_user" in
    0)
        printf '%s\n' "Administrator '$admin_username' already exists; keeping its password unchanged."
        ;;
    1)
        docker compose exec app varys create-admin --username "$admin_username"
        ;;
    *)
        printf '%s\n' 'Could not check the administrator account.' >&2
        exit "$existing_user"
        ;;
esac

printf '%s\n' ''
printf '%s\n' 'Varys is ready at http://localhost:8000/login'
printf '%s\n' 'Use make compose-down when you are finished.'
