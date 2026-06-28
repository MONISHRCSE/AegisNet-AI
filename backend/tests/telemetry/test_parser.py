import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.telemetry.parser import parse_conn_log_line, NetworkFlowEvent


# ── Parser Unit Tests ────────────────────────────────────────────────────────

VALID_LINE = (
    "1715762400.000000\tCHhAvVGS1\t192.168.1.55\t54321\t10.0.0.8\t22\t"
    "tcp\tssh\t0.500000\t1200\t843\tSF\t-\t-\t0\tShADadFf\t10\t1600\t8\t1100\t-"
)

COMMENT_LINE = "#fields\tts\tuid\tid.orig_h"
SHORT_LINE = "1715762400.000000\tCHhAvVGS1\t192.168.1.55"


def test_parse_valid_conn_line():
    event = parse_conn_log_line(VALID_LINE)
    assert event is not None
    assert isinstance(event, NetworkFlowEvent)
    assert event.meta.source_ip == "192.168.1.55"
    assert event.meta.dest_ip == "10.0.0.8"
    assert event.meta.dest_port == 22
    assert event.proto == "tcp"
    assert event.service == "ssh"
    assert event.orig_bytes == 1200
    assert event.resp_bytes == 843
    assert event.conn_state == "SF"
    assert event.orig_pkts == 10
    assert event.resp_pkts == 8
    assert len(event.log_hash) == 64  # SHA-256 hex


def test_parse_comment_line_returns_none():
    assert parse_conn_log_line(COMMENT_LINE) is None


def test_parse_short_line_returns_none():
    assert parse_conn_log_line(SHORT_LINE) is None


def test_parse_empty_line_returns_none():
    assert parse_conn_log_line("") is None


def test_log_hash_is_deterministic():
    event1 = parse_conn_log_line(VALID_LINE)
    event2 = parse_conn_log_line(VALID_LINE)
    assert event1.log_hash == event2.log_hash


def test_to_redis_record_all_strings():
    event = parse_conn_log_line(VALID_LINE)
    record = event.to_redis_record()
    for key, value in record.items():
        assert isinstance(value, str), f"Field '{key}' is not a string: {type(value)}"


def test_to_mongo_doc_structure():
    event = parse_conn_log_line(VALID_LINE)
    doc = event.to_mongo_doc()
    assert "timestamp" in doc
    assert "meta" in doc
    assert "source_ip" in doc["meta"]
    assert "log_hash" in doc
    assert doc["log_hash"] == event.log_hash
