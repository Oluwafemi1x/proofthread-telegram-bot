from proofthread.links import telegram_message_link


def test_public_group_link() -> None:
    assert telegram_message_link(-100123, "proofthread_group", 77) == (
        "https://t.me/proofthread_group/77"
    )


def test_private_supergroup_link() -> None:
    assert telegram_message_link(-1009876543210, None, 42) == ("https://t.me/c/9876543210/42")


def test_basic_group_has_no_stable_link() -> None:
    assert telegram_message_link(-123456, None, 42) is None
