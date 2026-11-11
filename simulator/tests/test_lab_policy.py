import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_policy import decide_remediation, verify_recovery


def test_authorizes_only_exact_known_lab_link():
    loc = {"status": "candidate_found", "suspected_link_id": "s1-s2"}
    assert decide_remediation(loc, injected_link="s1-s2", allowed_links={"s1-s2"})["authorized"]


def test_wrong_inference_blocks_action():
    loc = {"status": "candidate_found", "suspected_link_id": "s2-s3"}
    assert not decide_remediation(loc, injected_link="s1-s2", allowed_links={"s1-s2"})["authorized"]


def test_ambiguity_blocks_action():
    assert not decide_remediation({"status": "ambiguous", "suspected_link_id": None},
                                  injected_link="s1-s2", allowed_links={"s1-s2"})["authorized"]


def test_verification_requires_observed_fault():
    assert not verify_recovery(0, 0, 0, 5)["passed"]
    assert verify_recovery(0, 30, 2, 5)["passed"]
    assert not verify_recovery(0, 30, 20, 5)["passed"]
