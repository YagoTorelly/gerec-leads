from gerec_api.auth.permissions import PermissionDenied, PermissionService
from gerec_api.auth.sessions import CurrentUser


def test_seller_scope_cannot_be_widened_by_a_requested_seller_id():
    seller = CurrentUser("seller-1", "seller@example.test", "seller")
    query = PermissionService.scope_query(seller, "leads")
    assert query["$or"][0]["assigneeId"]["$in"][0] == "seller-1"
    assert query["$or"][1]["historicalSellerIds"]["$in"][0] == "seller-1"


def test_admin_scope_is_global_and_seller_cannot_run_admin_commands():
    admin = CurrentUser("admin-1", "admin@example.test", "admin")
    assert PermissionService.scope_query(admin, "leads") == {}
    try:
        PermissionService.require_admin(CurrentUser("s", "s@example.test", "seller"))
    except PermissionDenied:
        pass
    else:
        raise AssertionError("seller unexpectedly authorized")
