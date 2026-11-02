from collections import namedtuple

from redash import models
from redash.permissions import has_access
from tests import BaseTestCase

MockUser = namedtuple("MockUser", ["permissions", "group_ids"])
view_only = True


class TestHasAccess(BaseTestCase):
    def test_allows_admin_regardless_of_groups(self):
        user = MockUser(["admin"], [])

        self.assertTrue(has_access({}, user, view_only))
        self.assertTrue(has_access({}, user, not view_only))

    def test_allows_if_user_member_in_group_with_view_access(self):
        user = MockUser([], [1])

        self.assertTrue(has_access({1: view_only}, user, view_only))

    def test_allows_if_user_member_in_group_with_full_access(self):
        user = MockUser([], [1])

        self.assertTrue(has_access({1: not view_only}, user, not view_only))

    def test_allows_if_user_member_in_multiple_groups(self):
        user = MockUser([], [1, 2, 3])

        self.assertTrue(has_access({1: not view_only, 2: view_only}, user, not view_only))
        self.assertFalse(has_access({1: view_only, 2: view_only}, user, not view_only))
        self.assertTrue(has_access({1: view_only, 2: view_only}, user, view_only))
        self.assertTrue(has_access({1: not view_only, 2: not view_only}, user, view_only))

    def test_not_allows_if_not_enough_permission(self):
        user = MockUser([], [1])

        self.assertFalse(has_access({1: view_only}, user, not view_only))
        self.assertFalse(has_access({2: view_only}, user, not view_only))
        self.assertFalse(has_access({2: view_only}, user, view_only))
        self.assertFalse(has_access({2: not view_only, 1: view_only}, user, not view_only))

    def test_allows_access_to_query_by_query_api_key(self):
        query = self.factory.create_query()
        user = models.ApiUser(query.api_key, None, [])

        self.assertTrue(has_access(query, user, view_only))

    def test_doesnt_allow_access_to_query_by_different_api_key(self):
        query = self.factory.create_query()
        other_query = self.factory.create_query()
        user = models.ApiUser(other_query.api_key, None, [])

        self.assertFalse(has_access(query, user, view_only))

    def test_allows_access_to_query_by_dashboard_api_key(self):
        dashboard = self.factory.create_dashboard()
        visualization = self.factory.create_visualization()
        self.factory.create_widget(dashboard=dashboard, visualization=visualization)
        query = self.factory.create_query(visualizations=[visualization])

        api_key = self.factory.create_api_key(object=dashboard).api_key
        user = models.ApiUser(api_key, None, [])

        self.assertTrue(has_access(query, user, view_only))

    def test_allows_dynamic_token_to_run_queries_on_its_dashboard(self):
        dashboard = self.factory.create_dashboard()
        widget = self.factory.create_widget(dashboard=dashboard)
        query = widget.visualization.query_rel
        user = models.ApiUser("token", self.factory.org, [], obj=dashboard, dynamic=True)

        self.assertTrue(has_access(query, user, view_only))
        # Unlike stored public links, dynamic tokens may run queries with text parameters.
        self.assertTrue(has_access(query, user, not view_only))

    def test_doesnt_allow_dynamic_token_to_run_queries_off_its_dashboard(self):
        dashboard = self.factory.create_dashboard()
        self.factory.create_widget(dashboard=dashboard)
        other_query = self.factory.create_widget().visualization.query_rel
        user = models.ApiUser("token", self.factory.org, [], obj=dashboard, dynamic=True)

        self.assertFalse(has_access(other_query, user, view_only))

    def test_doesnt_allow_dynamic_token_to_run_archived_queries(self):
        dashboard = self.factory.create_dashboard()
        query = self.factory.create_widget(dashboard=dashboard).visualization.query_rel
        query.is_archived = True
        user = models.ApiUser("token", self.factory.org, [], obj=dashboard, dynamic=True)

        self.assertFalse(has_access(query, user, view_only))

    def test_doesnt_allow_dynamic_token_from_other_org(self):
        dashboard = self.factory.create_dashboard()
        query = self.factory.create_widget(dashboard=dashboard).visualization.query_rel
        user = models.ApiUser("token", self.factory.create_org(), [], obj=dashboard, dynamic=True)

        self.assertFalse(has_access(query, user, view_only))
