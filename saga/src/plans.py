"""Fixed six-step plans (hand-written stand-ins for planner output; see README limitations)."""
from sandbox import ARGS

PLANS = {
    "release": [("git_create_branch", "rel"), ("git_commit_file", "CHANGELOG"), ("chat_post", "release started"),
                ("git_push", "rel"), ("webhook_notify", "https://ci.invalid/hook"), ("db_insert", "releases:r1")],
    "order": [("db_insert", "orders:o1"), ("pay_charge", "25"), ("email_send", "buyer@example.invalid"),
              ("db_update", "widget"), ("sms_send", "+10000000001"), ("cal_create", "delivery-slot")],
    "meeting": [("cal_create", "meeting"), ("email_send", "team@example.invalid"), ("db_insert", "rooms:b2"),
                ("chat_post", "meeting booked"), ("sms_send", "+10000000002"), ("git_commit_file", "minutes.md")],
}
IRREVERSIBLE = {"sms_send", "webhook_notify"}


def irreversible_last(plan):
    """Ordering rule: stable-move irreversible steps to the end (they then run only if all earlier steps succeeded)."""
    return [s for s in plan if s[0] not in IRREVERSIBLE] + [s for s in plan if s[0] in IRREVERSIBLE]
