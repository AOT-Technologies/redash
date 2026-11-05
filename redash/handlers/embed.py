from flask import abort, request
from flask_login import current_user, login_required

from redash import models, settings
from redash.authentication import get_user_from_dashboard_token
from redash.handlers import routes
from redash.handlers.base import get_object, org_scoped_rule, record_event
from redash.handlers.static import render_index
from redash.security import csp_allows_embeding
from redash.utils.dynamic_key import decode_token

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
    dashboard = None
    if current_user.is_api_user():
        # API calls from an open page accept a dynamic token for DASHBOARD_KEY_SESSION_PERIOD,
        # but the page itself can only be opened with a token younger than DASHBOARD_KEY_EXPIRY_PERIOD.
        if current_user.is_dynamic_token and not decode_token(
            current_user.id, max_age=settings.DASHBOARD_KEY_EXPIRY_PERIOD
        ):
            abort(404)
        dashboard = current_user.object
    else:
        api_key = get_object(models.ApiKey.get_by_api_key, token)
        if api_key:
            dashboard = api_key.object
        else:
            token_user = get_user_from_dashboard_token(
                token, current_org._get_current_object(), max_age=settings.DASHBOARD_KEY_EXPIRY_PERIOD
            )
            if token_user:
                dashboard = token_user.object

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
