#!/bin/sh
set -e

if [ -n "${POSTGRES_HOST:-}" ]; then
    echo "Aguardando PostgreSQL em ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    python -c "
import os, socket, time
host = os.environ['POSTGRES_HOST']
port = int(os.environ.get('POSTGRES_PORT', '5432'))
for _ in range(30):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit('PostgreSQL não respondeu a tempo.')
"
fi

python manage.py migrate --noinput

if [ "${AUTO_POPULAR_DEMO:-1}" = "1" ]; then
    python manage.py popular_demo --se-vazio
fi

exec gunicorn web.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --threads 1 \
    --access-logfile - \
    --error-logfile -
