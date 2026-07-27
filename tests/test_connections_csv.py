"""LinkedIn's own connections export is the free source of 1st-degree contacts.

Its real quirks drive these tests: a notes preamble before the header row, and
mostly-blank email addresses since LinkedIn stripped them.
"""

from backend.services.connections_csv import find_connections_at, load_connections

HEADER = "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"

# LinkedIn ships two notes lines and a blank line before the real header.
PREAMBLE = (
    "Notes:\n"
    '"When exporting your connection data, you may notice that some of the '
    'email addresses are missing. ..."\n'
    "\n"
)

ROWS = (
    "Asha,Rao,https://www.linkedin.com/in/asha-rao,,Zepto,SDE-2,01 Jan 2024\n"
    "Bhavya,Nair,https://www.linkedin.com/in/bhavya-nair,b@x.com,"
    "Zepto Marketplace Private Limited,Engineering Manager,02 Feb 2024\n"
    "Chetan,Iyer,https://www.linkedin.com/in/chetan-iyer,,Swiggy,SDE-1,03 Mar 2024\n"
)


def _write(tmp_path, text):
    path = tmp_path / "Connections.csv"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_reads_a_plain_export(tmp_path):
    contacts = load_connections(_write(tmp_path, HEADER + ROWS))

    assert len(contacts) == 3
    first = contacts[0]
    assert first["name"] == "Asha Rao"
    assert first["current_company"] == "Zepto"
    assert first["current_role"] == "SDE-2"
    assert first["linkedin_url"] == "https://www.linkedin.com/in/asha-rao"
    assert first["degree_type"] == "1st"      # everyone in your export is 1st degree
    assert first["source"] == "csv"


def test_skips_linkedins_notes_preamble(tmp_path):
    """Reading the file as-is would treat 'Notes:' as the header row."""
    contacts = load_connections(_write(tmp_path, PREAMBLE + HEADER + ROWS))
    assert len(contacts) == 3
    assert contacts[0]["name"] == "Asha Rao"


def test_keeps_an_email_when_linkedin_provides_one(tmp_path):
    contacts = load_connections(_write(tmp_path, HEADER + ROWS))
    assert contacts[0]["email"] is None            # blank in the export
    assert contacts[1]["email"] == "b@x.com"


def test_a_missing_export_is_not_an_error(tmp_path):
    """The CSV is optional; the referral hunt still works without it."""
    assert load_connections(str(tmp_path / "nope.csv")) == []


def test_finds_contacts_at_a_company(tmp_path):
    path = _write(tmp_path, HEADER + ROWS)
    assert [c["name"] for c in find_connections_at(path, "Swiggy")] == ["Chetan Iyer"]


def test_company_match_survives_legal_suffixes(tmp_path):
    """A job says 'Zepto'; the CSV says 'Zepto Marketplace Private Limited'."""
    names = [c["name"] for c in find_connections_at(_write(tmp_path, HEADER + ROWS), "Zepto")]
    assert names == ["Asha Rao", "Bhavya Nair"]


def test_company_match_ignores_case(tmp_path):
    assert len(find_connections_at(_write(tmp_path, HEADER + ROWS), "zEpTo")) == 2


def test_unknown_company_returns_nothing(tmp_path):
    assert find_connections_at(_write(tmp_path, HEADER + ROWS), "Google") == []


def test_rows_missing_a_name_are_skipped(tmp_path):
    text = HEADER + ",,https://linkedin.com/in/ghost,,Zepto,SDE,01 Jan 2024\n" + ROWS
    assert len(load_connections(_write(tmp_path, text))) == 3
