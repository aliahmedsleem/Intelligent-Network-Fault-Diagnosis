"""Static contracts runnable without Mininet installed."""
import ast
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "mininet_experiment.py"


def test_script_parses():
    ast.parse(SCRIPT.read_text(encoding="utf-8"))


def test_measurement_labels():
    code = SCRIPT.read_text(encoding="utf-8")
    assert '"mininet_measured"' in code
    assert '"analytical_estimate"' not in code
    assert "iperf3" in code and "ping" in code and "netem" in code
