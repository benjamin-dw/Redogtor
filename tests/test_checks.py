"""Tests for the built-in security and update check. No internet needed: the outside answers are faked.
Run: python tests/test_checks.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("REDACTOR_HOSTED", "1")
import app as redogtor  # noqa: E402

C = redogtor.app.test_client()
INSTALLED = {"spacy": "3.8.2", "flask": "3.0.0", "pymupdf": "1.24.0", redogtor._norm(redogtor.MODEL): "3.8.0"}


def fake(answers):
    def get(url, body=None):
        for key, val in answers.items():
            if key in url:
                if isinstance(val, Exception):
                    raise val
                return val
        raise OSError("no fake for " + url)
    return get


def run(answers, installed=INSTALLED):
    redogtor._get_json = fake(answers)
    redogtor._installed = lambda: dict(installed)
    return redogtor.run_checks()


OSV_NONE = {"results": [{} for _ in INSTALLED]}
COMPAT = {"spacy": {"3.8": {redogtor.MODEL: ["3.8.0"]}}}


def pypi(versions):
    return {"pypi.org/pypi/%s/" % k: {"info": {"version": v}} for k, v in versions.items()}


def test_all_clear():
    got = run({"querybatch": OSV_NONE, "compatibility.json": COMPAT,
               **pypi({"spacy": "3.8.2", "flask": "3.0.0", "pymupdf": "1.24.0"})})
    assert got["state"] == "all clear" and not got["problems"], got


def test_security_hole_and_updates_found():
    names = sorted(INSTALLED)
    osv = {"results": [{"vulns": [{"id": "GHSA-test"}]} if n == "flask" else {} for n in names]}
    detail = {"summary": "Bad thing", "affected": [{"package": {"name": "flask"},
              "ranges": [{"events": [{"introduced": "0"}, {"fixed": "3.0.3"}]}]}]}
    compat = {"spacy": {"3.8": {redogtor.MODEL: ["3.8.0", "3.8.1"]}}}
    got = run({"querybatch": osv, "vulns/GHSA-test": detail, "compatibility.json": compat,
               **pypi({"spacy": "3.9.0", "flask": "3.0.3", "pymupdf": "1.24.0"})})
    assert got["state"] == "security fixes needed", got
    assert got["security"][0]["package"] == "flask" and got["security"][0]["fixed_in"] == ["3.0.3"], got
    assert {u["package"] for u in got["updates"]} == {"spacy", "flask"}, got
    assert got["model"]["newer"] and got["model"]["newest_for_your_spacy"] == "3.8.1", got


def test_offline_is_never_all_clear():
    got = run({"querybatch": OSError("offline"), "pypi.org": OSError("offline"),
               "compatibility.json": OSError("offline")})
    assert got["state"] == "could not fully check" and got["problems"], got
    got = run({}, installed={})
    assert got["state"] == "could not fully check", got


def test_status_is_for_this_machine_only():
    assert C.get("/status").status_code == 200
    assert C.get("/status", headers={"CF-Connecting-IP": "203.0.113.9"}).status_code == 404
    assert C.get("/status", environ_base={"REMOTE_ADDR": "203.0.113.9"}).status_code == 404
    assert C.post("/status/check", headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 404
    assert C.get("/health").get_json() == {"ok": True}       # the public health check says nothing more


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok  ", name)
    print("%d passed" % n)
