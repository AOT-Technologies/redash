"""
Utils for dynamic key.
"""

from typing import Dict

from itsdangerous import BadData, URLSafeTimedSerializer

from redash import settings
from redash.worker import get_job_logger

logger = get_job_logger(__name__)


def generate_token(dashboard_id: int, user_id: int) -> str:
    """Generate a token based on the dashboard and user id."""
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    token = {"id": dashboard_id, "user": user_id}
    dynamic_key = serializer.dumps(token, salt=settings.DATASOURCE_SECRET_KEY)
    return dynamic_key


def decode_token(dynamic_key: str, max_age: int = None) -> Dict[str, int]:
    """Decode the dynamically generated token; returns {} if it is invalid or older than max_age seconds."""
    if max_age is None:
        max_age = settings.DASHBOARD_KEY_EXPIRY_PERIOD

    try:
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        decode_json = serializer.loads(dynamic_key, salt=settings.DATASOURCE_SECRET_KEY, max_age=int(max_age))
    except BadData:
        # Every unknown API key passes through here, so this is not an error.
        logger.debug("Dynamic dashboard token is invalid or expired")
        return {}

    if not isinstance(decode_json, dict):
        return {}

    return decode_json
