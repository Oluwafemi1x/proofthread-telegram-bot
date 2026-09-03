from __future__ import annotations

import shlex
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True, slots=True)
class ParsedAction:
    text: str
    owner_label: str | None
    due_at: datetime | None


class ActionSyntaxError(ValueError):
    pass


def parse_action_args(raw: str | None, timezone_name: str = "UTC") -> ParsedAction:
    """Parse: [YYYY-MM-DD|-] [@owner|me|-] task text."""

    if not raw:
        raise ActionSyntaxError("Add a due date, owner and task description.")
    try:
        tokens = shlex.split(raw)
    except ValueError as exc:
        raise ActionSyntaxError("Check the quotation marks in the action.") from exc
    if len(tokens) < 3:
        raise ActionSyntaxError("Use: /action YYYY-MM-DD @owner Task description")

    due_token, owner_token, *text_tokens = tokens
    due_at = None
    if due_token != "-":
        try:
            day = datetime.strptime(due_token, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ActionSyntaxError("Due date must use YYYY-MM-DD, or '-' for no date.") from exc
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ActionSyntaxError(f"Unknown timezone: {timezone_name}") from exc
        due_at = datetime.combine(day, time(17, 0), timezone)

    owner_label = None if owner_token == "-" else owner_token
    if owner_label and owner_label != "me" and not owner_label.startswith("@"):
        raise ActionSyntaxError("Owner must be @username, 'me', or '-'.")

    text = " ".join(text_tokens).strip()
    if len(text) < 3:
        raise ActionSyntaxError("Task description must contain at least 3 characters.")
    return ParsedAction(text=text, owner_label=owner_label, due_at=due_at)
