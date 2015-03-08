import json
import os
import urlparse


def parse_db_url(url):
    url_parts = urlparse.urlparse(url)
    connection = {'threadlocals': True}

    if url_parts.hostname and not url_parts.path:
        connection['name'] = url_parts.hostname
    else:
        connection['name'] = url_parts.path[1:]
        connection['host'] = url_parts.hostname
        connection['port'] = url_parts.port
        connection['user'] = url_parts.username
        connection['password'] = url_parts.password

    return connection


def fix_assets_path(path):
    fullpath = os.path.join(os.path.dirname(__file__), path)
    return fullpath


def array_from_string(str):
    array = str.split(',')
    if "" in array:
        array.remove("")

    return array


def parse_boolean(str):
    return json.loads(str.lower())


NAME = os.environ.get('APP_NAME', 'App')

REDIS_URL = os.environ.get('APP_REDIS_URL', "redis://localhost:6379/0")

STATSD_HOST = os.environ.get('APP_STATSD_HOST', "127.0.0.1")
STATSD_PORT = int(os.environ.get('APP_STATSD_PORT', "8125"))
STATSD_PREFIX = os.environ.get('APP_STATSD_PREFIX', "app")

# The following is kept for backward compatability, and shouldn't be used any more.
CONNECTION_ADAPTER = os.environ.get("APP_CONNECTION_ADAPTER", "pg")
CONNECTION_STRING = os.environ.get("APP_CONNECTION_STRING", "user= password= host= port=5439 dbname=")

# Connection settings for the app's own database (where we store the queries, results, etc)
DATABASE_CONFIG = parse_db_url(os.environ.get("APP_DATABASE_URL", "postgresql://postgres"))

# Celery related settings
CELERY_BROKER = os.environ.get("APP_CELERY_BROKER", REDIS_URL)
CELERY_BACKEND = os.environ.get("APP_CELERY_BACKEND", REDIS_URL)
CELERY_FLOWER_URL = os.environ.get("APP_CELERY_FLOWER_URL", "/flower")

# The following enables periodic job (every 5 minutes) of removing unused query results. Behind this "feature flag" until
# proved to be "safe".
# THIS IS AN EXAMPLE FOR THE CELERY TASKS
QUERY_RESULTS_CLEANUP_ENABLED = parse_boolean(os.environ.get("APP_QUERY_RESULTS_CLEANUP_ENABLED", "false"))

STATIC_ASSETS_PATH = fix_assets_path(os.environ.get("APP_STATIC_ASSETS_PATH", "../rd_ui/app/"))
WORKERS_COUNT = int(os.environ.get("APP_WORKERS_COUNT", "2"))
JOB_EXPIRY_TIME = int(os.environ.get("APP_JOB_EXPIRY_TIME", 3600 * 6))
LOG_LEVEL = os.environ.get("APP_LOG_LEVEL", "INFO")