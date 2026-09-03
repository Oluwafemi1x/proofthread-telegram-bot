def telegram_message_link(chat_id: int, username: str | None, message_id: int) -> str | None:
    """Build a Telegram source link for public or private supergroups."""

    if username:
        return f"https://t.me/{username.lstrip('@')}/{message_id}"
    value = str(chat_id)
    if value.startswith("-100"):
        return f"https://t.me/c/{value[4:]}/{message_id}"
    return None
