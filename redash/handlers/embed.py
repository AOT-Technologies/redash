from flask import request, abort

from .authentication import current_org

from flask_login import current_user, login_required

from redash import models

from redash.handlers import routes

from redash.handlers.base import get_object, org_scoped_rule, record_event

from redash.handlers.base import (
    get_object_or_404,
    org_scoped_rule,
    record_event,
)
from redash.handlers.static import render_index
from redash.security import csp_allows_embeding
from redash.worker import get_job_logger
from redash.utils.dynamic_key import decode_token

logger = get_job_logger(__name__)

from .authentication import current_org


@routes.route(
    org_scoped_rule("/embed/query/<query_id>/visualization/<visualization_id>"),
    methods=["GET"],
)
@login_required
@csp_allows_embeding
def embed(query_id, visualization_id, org_slug=None):
    record_event(
        current_org,
        current_user._get_current_object(),
        {
            "action": "view",
            "object_id": visualization_id,
            "object_type": "visualization",
            "query_id": query_id,
            "embed": True,
            "referer": request.headers.get("Referer"),
        },
    )
    return render_index()


@routes.route(org_scoped_rule("/public/dashboards/<token>"), methods=["GET"])
@login_required
@csp_allows_embeding
def public_dashboard(token, org_slug=None):
    logger.info(f"Inside >>> public_dashboard : {token}")
    logger.info(f"current_user.is_api_user() : {current_user.is_api_user()}")
    if current_user.is_api_user():
        dashboard = current_user.object

    else:
        api_key = get_object(models.ApiKey.get_by_api_key, token)
        logger.info(f" api_key : {api_key}")
        if api_key:
            dashboard = api_key.object
            logger.info('dashboard %s', dashboard)
        else:
            # Here if the object is not found using the api_key try to decode the token using salt and see if it's valid
            decoded_token = decode_token(token)
            logger.info(f" decoded_token : {decoded_token}")
            if decode_token:
                dashboard_id = decoded_token.get('id')
                logger.info('Extracted dashboard id from the token : %s', dashboard_id)
                dashboard = models.Dashboard.get_by_id(dashboard_id)
                logger.info('Found dashboard : %s', dashboard)

    logger.info('dashboard >> %s', dashboard)
    if not dashboard:
        abort(404)

    record_event(
        current_org,
        current_user,
        {
            "action": "view",
            "object_id": dashboard.id,
            "object_type": "dashboard",
            "public": True,
            "headless": "embed" in request.args,
            "referer": request.headers.get("Referer"),
        },
    )
    return render_index()
