from mock import patch

from redash import settings
from redash.models import db
from redash.utils.dynamic_key import generate_token
from tests import BaseTestCase


class TestUnembedables(BaseTestCase):
    def test_not_embedable(self):
        query = self.factory.create_query()
        res = self.make_request("get", "/api/queries/{0}".format(query.id))
        self.assertEqual(res.status_code, 200)
        # The fork's default CSP lets formsflow (*.aot-technologies.com) frame the app, but nobody else.
        csp = res.headers["Content-Security-Policy"]
        self.assertIn("frame-ancestors 'self' *.aot-technologies.com", csp)
        self.assertNotIn("frame-ancestors *", csp)
        # X-Frame-Options is not set by default (REDASH_FRAME_OPTIONS is empty); CSP frame-ancestors governs framing.
        self.assertNotIn("X-Frame-Options", res.headers)


class TestEmbedVisualization(BaseTestCase):
    def test_sucesss(self):
        vis = self.factory.create_visualization()
        vis.query_rel.latest_query_data = self.factory.create_query_result()
        db.session.add(vis.query_rel)

        res = self.make_request(
            "get",
            "/embed/query/{}/visualization/{}".format(vis.query_rel.id, vis.id),
            is_json=False,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("frame-ancestors *", res.headers["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", res.headers)


# TODO: this should be applied to the new API endpoint
class TestPublicDashboard(BaseTestCase):
    def test_success(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard)

        res = self.make_request(
            "get",
            "/public/dashboards/{}".format(api_key.api_key),
            user=False,
            is_json=False,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("frame-ancestors *", res.headers["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", res.headers)

    def test_works_for_logged_in_user(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard)

        res = self.make_request("get", "/public/dashboards/{}".format(api_key.api_key), is_json=False)
        self.assertEqual(res.status_code, 200)

    def test_bad_token(self):
        res = self.make_request("get", "/public/dashboards/bad-token", user=False, is_json=False)
        self.assertEqual(res.status_code, 302)

    def test_inactive_token(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard, active=False)
        res = self.make_request(
            "get",
            "/public/dashboards/{}".format(api_key.api_key),
            user=False,
            is_json=False,
        )
        self.assertEqual(res.status_code, 302)

    def test_dynamic_token(self):
        dashboard = self.factory.create_dashboard()
        token = generate_token(dashboard.id, self.factory.user.id)

        res = self.make_request("get", "/public/dashboards/{}".format(token), user=False, is_json=False)
        self.assertEqual(res.status_code, 200)

    def test_dynamic_token_too_old_to_open_the_page(self):
        dashboard = self.factory.create_dashboard()
        token = generate_token(dashboard.id, self.factory.user.id)

        with patch.object(settings, "DASHBOARD_KEY_EXPIRY_PERIOD", -1):
            res = self.make_request("get", "/public/dashboards/{}".format(token), user=False, is_json=False)
        self.assertEqual(res.status_code, 404)

    # Not relevant for now, as tokens in api_keys table are only created for dashboards. Once this changes, we should
    # add this test.
    # def test_token_doesnt_belong_to_dashboard(self):
    #     pass


class TestAPIPublicDashboard(BaseTestCase):
    def test_success(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard)

        res = self.make_request(
            "get",
            "/api/dashboards/public/{}".format(api_key.api_key),
            user=False,
            is_json=False,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("frame-ancestors *", res.headers["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", res.headers)

    def test_works_for_logged_in_user(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard)

        res = self.make_request("get", "/api/dashboards/public/{}".format(api_key.api_key), is_json=False)
        self.assertEqual(res.status_code, 200)

    def test_bad_token(self):
        res = self.make_request("get", "/api/dashboards/public/bad-token", user=False, is_json=False)
        self.assertEqual(res.status_code, 404)

    def test_inactive_token(self):
        dashboard = self.factory.create_dashboard()
        api_key = self.factory.create_api_key(object=dashboard, active=False)
        res = self.make_request(
            "get",
            "/api/dashboards/public/{}".format(api_key.api_key),
            user=False,
            is_json=False,
        )
        self.assertEqual(res.status_code, 404)

    def test_dynamic_token_keeps_working_after_the_page_is_open(self):
        dashboard = self.factory.create_dashboard()
        token = generate_token(dashboard.id, self.factory.user.id)

        # Older than DASHBOARD_KEY_EXPIRY_PERIOD, but within DASHBOARD_KEY_SESSION_PERIOD.
        with patch.object(settings, "DASHBOARD_KEY_EXPIRY_PERIOD", -1):
            res = self.make_request("get", "/api/dashboards/public/{}".format(token), user=False, is_json=False)
        self.assertEqual(res.status_code, 200)

    def test_expired_dynamic_token(self):
        dashboard = self.factory.create_dashboard()
        token = generate_token(dashboard.id, self.factory.user.id)

        with patch.object(settings, "DASHBOARD_KEY_SESSION_PERIOD", -1):
            res = self.make_request("get", "/api/dashboards/public/{}".format(token), user=False, is_json=False)
        self.assertEqual(res.status_code, 404)

    # Not relevant for now, as tokens in api_keys table are only created for dashboards. Once this changes, we should
    # add this test.
    # def test_token_doesnt_belong_to_dashboard(self):
    #     pass
