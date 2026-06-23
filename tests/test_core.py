from logtriage.core import analyze, fingerprint, parse_line


def test_parses_plain_text_level():
    result = parse_line("2024-01-01 12:00:00 ERROR something broke")
    assert result.level == "ERROR"


def test_parses_json_log():
    result = parse_line('{"level": "WARN", "message": "disk almost full"}')
    assert result.level == "WARN"
    assert result.message == "disk almost full"


def test_warning_normalizes_to_warn():
    assert parse_line("2024-01-01 WARNING disk almost full").level == "WARN"


def test_line_without_level():
    assert parse_line("just some text").level is None


def test_fingerprint_clusters_similar_errors():
    a = fingerprint("Timeout connecting to host 10.0.0.1 after 3000 ms")
    b = fingerprint("Timeout connecting to host 10.0.0.9 after 5000 ms")
    assert a == b


def test_fingerprint_masks_uuid_and_quotes():
    fp = fingerprint('User "alice" with id 550e8400-e29b-41d4-a716-446655440000 failed')
    assert "<uuid>" in fp
    assert "<str>" in fp


def test_analyze_counts_and_clusters():
    lines = [
        "INFO starting up",
        "ERROR Timeout connecting to host 10.0.0.1 after 3000 ms",
        "ERROR Timeout connecting to host 10.0.0.2 after 4000 ms",
        "FATAL out of memory",
        "",  # blank lines ignored
    ]
    report = analyze(lines)
    assert report.total == 4
    assert report.level_counts["ERROR"] == 2
    assert report.error_count == 3  # 2 ERROR + 1 FATAL
    # The two timeouts should collapse into a single cluster.
    assert report.error_clusters.most_common(1)[0][1] == 2
