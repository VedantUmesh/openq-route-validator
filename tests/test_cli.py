import json

from openq_route_validator.cli import main


def test_legacy_find_invocation_keeps_text_output(capsys):
    assert main(["--initial", "000", "--target", "111"]) == 0
    output = capsys.readouterr().out
    assert "Found 3 step(s):" in output
    assert "Step 3: X(2) -> |111>" in output


def test_find_json_output_is_machine_readable(capsys):
    assert main(["find", "--initial", "000", "--target", "111", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == 1
    assert payload["gates"] == ["X(0)", "X(1)", "X(2)"]
    assert payload["states"][-1] == "111"


def test_validate_command_accepts_custom_edges_and_reports_json(capsys):
    args = [
        "validate",
        "--nodes",
        "2",
        "--edge",
        "0->1",
        "--initial",
        "10",
        "--target",
        "11",
        "--gate",
        "CNOT(0,1)",
        "--format",
        "json",
    ]
    assert main(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["states"] == ["10", "11"]


def test_json_errors_are_structured(capsys):
    assert main(["find", "--initial", "00", "--format", "json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "invalid_state"
