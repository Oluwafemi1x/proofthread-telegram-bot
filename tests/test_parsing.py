from datetime import datetime

import pytest

from proofthread.parsing import ActionSyntaxError, parse_action_args


def test_parse_complete_action() -> None:
    result = parse_action_args("2026-12-10 @femi Ship the release", "Africa/Lagos")

    assert result.text == "Ship the release"
    assert result.owner_label == "@femi"
    assert result.due_at == datetime.fromisoformat("2026-12-10T17:00:00+01:00")


def test_parse_action_without_due_date_or_owner() -> None:
    result = parse_action_args("- - Review architecture")

    assert result.text == "Review architecture"
    assert result.owner_label is None
    assert result.due_at is None


@pytest.mark.parametrize(
    "value",
    [None, "tomorrow @femi Fix it", "2026-10-10 femi Fix it", "2026-10-10 @femi"],
)
def test_reject_invalid_action_syntax(value: str | None) -> None:
    with pytest.raises(ActionSyntaxError):
        parse_action_args(value)
