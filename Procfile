web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --max-requests-jitter 100 --preload app:app
release: python scripts/setup_production.py