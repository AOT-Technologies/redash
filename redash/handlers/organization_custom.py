from flask import request

from redash import models
from redash.handlers.base import BaseResource
from redash.permissions import (
    require_admin,
)
from redash.worker import get_job_logger

logger = get_job_logger(__name__)


class OrganizationResource(BaseResource):
    @require_admin
    def post(self):
        """
        Creates a new organization.

        """
        org_payload = request.get_json(force=True)
        # The payload carries the admin password and the system user's API key, so only log the slug.
        logger.info("Creating new organization %s", org_payload.get("slug"))
        org = models.Organization(
            name=org_payload["name"],
            slug=org_payload["slug"],
            settings={
                "settings": {
                    "auth_password_login_enabled": True,
                    "auth_saml_enabled": False,
                    "auth_saml_type": "dynamic",
                    "auth_saml_entity_id": "redash",
                    "auth_saml_metadata_url": f"{org_payload['samlDescriptor']}",
                    "auth_saml_nameid_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    "auth_saml_sso_url": "",
                    "auth_saml_x509_cert": "",
                    "date_format": "DD/MM/YY",
                    "time_format": "HH:mm",
                    "integer_format": "0,0",
                    "float_format": "0,0.00",
                    "multi_byte_search_enabled": False,
                    "auth_jwt_login_enabled": False,
                    "auth_jwt_auth_issuer": "",
                    "auth_jwt_auth_public_certs_url": "",
                    "auth_jwt_auth_audience": "",
                    "auth_jwt_auth_algorithms": ["HS256", "RS256", "ES256"],
                    "auth_jwt_auth_cookie_name": "",
                    "auth_jwt_auth_header_name": "",
                    "feature_show_permissions_control": False,
                    "send_email_on_failed_scheduled_queries": False,
                    "hide_plotly_mode_bar": False,
                    "disable_public_urls": False,
                },
                "google_apps_domains": [],
            },
        )

        admin_group = models.Group(
            name=f"{org.slug}-admin",
            permissions=[*models.Group.DEFAULT_PERMISSIONS, "admin"],
            org=org,
            type=models.Group.REGULAR_GROUP,
        )

        # default_group = models.Group(
        #     name="default",
        #     permissions=models.Group.DEFAULT_PERMISSIONS,
        #     org=org,
        #     type=models.Group.BUILTIN_GROUP,
        # )

        models.db.session.add_all([org, admin_group])
        models.db.session.commit()

        # Create a system user for accessing through API.
        system_user = models.User(
            org=org,
            name="system",
            email=f"system@{org.slug}",
            group_ids=[admin_group.id],
            api_key=org_payload.get("userApiKey", ""),
        )

        user = models.User(
            org=org,
            name=org_payload["userName"],
            email=org_payload["email"],
            group_ids=[admin_group.id],
        )
        user.hash_password(org_payload.get("password", ""))

        models.db.session.add_all([user, system_user])
        models.db.session.commit()
        logger.info("Finished creating Org")
