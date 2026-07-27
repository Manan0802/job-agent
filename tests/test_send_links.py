"""Handing the user a ready-to-send message — without sending it.

The project bans auto-DM and auto-apply outright: LinkedIn had AIHawk pulled
for exactly that, and the account at risk here is the user's own. So every
path ends with a link the user clicks and a body they send themselves.
"""

from urllib.parse import parse_qs, unquote, urlparse

from backend.schemas.outreach import OutreachDraft
from backend.services import send_links

DM = OutreachDraft(
    message="Hey Asha!\n\nSaw we both went to DTU. Would you be open to referring me?\n\n- Manan",
    tone="casual", message_type="alumni_dm", channel="linkedin_dm",
)

EMAIL = OutreachDraft(
    message="Hi Asha,\n\nI saw the SDE-2 role at Zepto...\n\nManan",
    subject="Quick question about the SDE-2 role", tone="professional",
    message_type="email_outreach", channel="email",
)

CONTACT = {"name": "Asha Rao", "linkedin_url": "https://linkedin.com/in/asha-rao",
           "email": "asha@example.com"}


def test_a_dm_hands_back_the_profile_to_open_and_the_text_to_paste():
    hand_off = send_links.build_send_link(DM, CONTACT)

    assert hand_off["action"] == "open_and_paste"
    assert hand_off["url"] == "https://linkedin.com/in/asha-rao"
    assert hand_off["copy_text"] == DM.message


def test_an_email_opens_the_users_own_mail_client_prefilled():
    hand_off = send_links.build_send_link(EMAIL, CONTACT)

    assert hand_off["action"] == "open_mail_client"
    assert hand_off["url"].startswith("mailto:asha@example.com")

    query = parse_qs(urlparse(hand_off["url"]).query)
    assert query["subject"][0] == EMAIL.subject
    assert "SDE-2 role at Zepto" in query["body"][0]


def test_line_breaks_survive_into_the_mail_client():
    """A naively built mailto turns the message into one run-on paragraph."""
    url = send_links.build_send_link(EMAIL, CONTACT)["url"]
    assert "\n" in unquote(url.split("body=", 1)[1])


def test_an_email_draft_without_an_address_falls_back_to_the_profile():
    hand_off = send_links.build_send_link(EMAIL, {**CONTACT, "email": None})

    assert hand_off["action"] == "open_and_paste"
    assert hand_off["url"] == CONTACT["linkedin_url"]


def test_a_contact_with_no_link_at_all_still_gets_the_text():
    hand_off = send_links.build_send_link(DM, {"name": "Asha Rao"})

    assert hand_off["url"] is None
    assert hand_off["copy_text"] == DM.message
    assert hand_off["instructions"]


def test_every_hand_off_explains_what_the_user_should_do():
    for draft, contact in ((DM, CONTACT), (EMAIL, CONTACT), (DM, {"name": "X"})):
        assert send_links.build_send_link(draft, contact)["instructions"]


def test_the_module_offers_no_way_to_send_anything_automatically():
    """A guard on the module surface: this file must never grow a sender."""
    surface = [name for name in dir(send_links) if not name.startswith("_")]
    assert not [n for n in surface if n.startswith(("send_", "auto_", "post_"))]
