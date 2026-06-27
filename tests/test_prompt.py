from vk_checker.models import CommunityData
from vk_checker.rules import extract_signals


def test_extract_signals_compact_data_without_html():
    data = CommunityData(url="https://vk.com/a", description="Пишите на test@example.com и https://t.me/example")
    signals = extract_signals(data)
    assert signals.emails == ["test@example.com"]
    assert signals.telegram_mentions
