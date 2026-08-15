#!/bin/sh
set -eu

python -c "from varys.config import load_settings; from varys.db import upgrade_database; settings = load_settings(); upgrade_database(settings.database_url or '')"
exec python -m varys.api
