"""Tests for the JSON API (/api/redact) that Leftward calls. Run: python tests/test_api.py
Needs the same packages as the app, including spaCy's English model."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("REDACTOR_HOSTED", "1")
os.environ.setdefault("REDACTOR_API", "1")
import app as redogtor  # noqa: E402

C = redogtor.app.test_client()
NOTE = ("Margaret Thibodeau called from Toronto Community Housing about the park. "
        "Call Margaret at 416-555-0199 or margaret@example.ca.")


def post(body, **kw):
    r = C.post("/api/redact", json=body, **kw)
    return r.status_code, r.get_json()


def test_default_is_names_only_and_keeps_organisations():
    st, got = post({"text": NOTE})
    assert st == 200, got
    t = got["text"]
    assert "Margaret" not in t and "Thibodeau" not in t, t
    assert "Toronto Community Housing" in t, t          # organisations are kept by default
    assert "416-555-0199" in t and "margaret@example.ca" in t, t   # only names unless asked
    assert got["redacted"] == ["names"] and got["api"] == 1 and got["counts"].get("NAME", 0) >= 2, got
    assert "[NAME 1]" in t, t                            # numbered by default, the same person keeps one number


def test_asked_groups_are_taken_out():
    st, got = post({"text": NOTE, "redact": ["names", "contact"]})
    assert st == 200 and "416-555-0199" not in got["text"] and "margaret@example.ca" not in got["text"], got
    assert "Toronto Community Housing" in got["text"], got
    st, got = post({"text": NOTE, "redact": ["names", "orgs"]})
    assert st == 200 and "Toronto Community Housing" not in got["text"], got


def test_many_texts_and_keep():
    st, got = post({"texts": [NOTE, "Nothing personal here."], "keep": ["Thibodeau"]})
    assert st == 200 and len(got["texts"]) == 2 and got["texts"][1] == "Nothing personal here.", got
    assert "Thibodeau" in got["texts"][0], got


def test_refuses_what_it_does_not_understand():
    for body in ({"text": NOTE, "redact": ["nmes"]},          # a typo never means "take out less"
                 {"text": NOTE, "redact": "names"},
                 {"text": NOTE, "colour": "red"},
                 {"text": NOTE, "texts": [NOTE]},
                 {},
                 {"texts": []},
                 {"text": 5},
                 {"text": NOTE, "number": "yes"},
                 {"text": NOTE, "keep": "Margaret"},
                 {"texts": ["a"] * (redogtor.API_MAX_TEXTS + 1)},
                 [NOTE]):
        st, got = post(body)
        assert st == 400 and "error" in got and "text" not in got and "texts" not in got, (body, st, got)
    r = C.post("/api/redact", data={"text": NOTE})
    assert r.status_code == 415, r.status_code
    r = C.post("/api/redact", data="{not json", content_type="application/json")
    assert r.status_code == 400, r.status_code


def test_health_and_page():
    got = C.get("/health").get_json()
    assert got["ok"] and got["api"] == 1 and got["default"] == ["names"], got
    page = C.get("/").get_data(as_text=True)
    assert 'id="orgs" checked' not in page and 'id="orgs"' in page and 'id="names" checked' in page


def test_api_is_off_unless_switched_on():
    redogtor.API_ON = False
    try:
        assert C.post("/api/redact", json={"text": NOTE}).status_code == 404
        assert "api" not in C.get("/health").get_json()
    finally:
        redogtor.API_ON = True


def test_api_never_answers_through_the_website():
    for h in ({"CF-Connecting-IP": "203.0.113.9"}, {"X-Forwarded-For": "203.0.113.9"}, {"CF-Ray": "abc"},
              {"Forwarded": "for=203.0.113.9"}):
        assert C.post("/api/redact", json={"text": NOTE}, headers=h).status_code == 404, h
        assert "api" not in C.get("/health", headers=h).get_json(), h
    r = C.post("/api/redact", json={"text": NOTE}, environ_base={"REMOTE_ADDR": "203.0.113.9"})
    assert r.status_code == 404
    old = redogtor.API_FROM
    redogtor.API_FROM = "127.0.0.1,172.17.0.0/16"
    try:
        r = C.post("/api/redact", json={"text": NOTE}, environ_base={"REMOTE_ADDR": "172.17.0.5"})
        assert r.status_code == 200, r.status_code
    finally:
        redogtor.API_FROM = old


def test_old_form_endpoint_unchanged():
    r = C.post("/redact", data={"text": NOTE, "names": "on", "number": "on"})
    got = r.get_json()
    assert r.status_code == 200 and "Margaret" not in got["text"] and "Toronto Community Housing" in got["text"], got


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok  ", name)
    print("%d passed" % n)
