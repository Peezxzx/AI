from backend.office_store import OfficeStore, route_command_reply


def make_store(tmp_path):
    store = OfficeStore(tmp_path / "office.db")
    store.ingest_snapshot(
        signal={"signal_id": "s1", "signal": "sell", "confidence": 1.0, "mt5_symbol": "XAUUSDm", "timeframe": "M15"},
        ea_status=None,
        runtime={"signal_id": "s1", "decision": "SKIP", "reason": "hard_magic_cap", "basket_profit": -15.7},
    )
    return store


def test_route_mt5_status_reply_uses_real_journal(tmp_path):
    store = make_store(tmp_path)

    reply = route_command_reply("สรุปสถานะ MT5 และ EA ตอนนี้", store)

    assert "XAUUSDm" in reply
    assert "SELL" in reply
    assert "SKIP" in reply
    assert "hard_magic_cap" in reply


def test_route_daily_brief_reply_contains_recommendation(tmp_path):
    store = make_store(tmp_path)

    reply = route_command_reply("สร้าง daily brief วันนี้", store)

    assert "Daily Brief" in reply
    assert "hard_magic_cap" in reply
    assert "Signals logged" in reply


def test_route_approval_list_reply_counts_waiting_items(tmp_path):
    store = make_store(tmp_path)
    store.record_command("buy XAUUSD now", source="test", target="mina")

    reply = route_command_reply("งานไหนต้อง approve", store)

    assert "1" in reply
    assert "Approve command: buy XAUUSD now" in reply
