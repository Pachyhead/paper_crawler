import time

from utils.timing_logger import get_file_logger, log_execution_time


def test_log_execution_time_writes_file(tmp_path):
    log_path = tmp_path / "logs" / "execution.log"
    target_url = "https://dblp.org/db/conf/emnlp/emnlp2025.html"

    with log_execution_time(
        "sample_block",
        log_path=log_path,
        context={"url": target_url},
    ):
        time.sleep(0.01)

    content = log_path.read_text(encoding="utf-8")
    assert "sample_block status=success elapsed_sec=" in content
    assert f"url={target_url}" in content


def test_log_execution_time_writes_failure_status(tmp_path):
    log_path = tmp_path / "logs" / "execution.log"

    try:
        with log_execution_time("failing_block", log_path=log_path):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError was not raised")

    content = log_path.read_text(encoding="utf-8")
    assert "failing_block status=failed elapsed_sec=" in content
    assert "error=RuntimeError:boom" in content


def test_get_file_logger_rotates_files(tmp_path):
    log_path = tmp_path / "logs" / "rotating.log"
    logger = get_file_logger(
        log_path=log_path,
        logger_name="rotating_test",
        max_bytes=200,
        backup_count=2,
    )

    for idx in range(100):
        logger.info("line=%s payload=%s", idx, "x" * 40)

    rotated_candidates = [log_path.with_suffix(".log.1"), log_path.with_suffix(".log.2")]
    assert any(path.exists() for path in rotated_candidates)


def test_get_file_logger_does_not_duplicate_handlers(tmp_path):
    log_path = tmp_path / "logs" / "dedupe.log"
    logger = get_file_logger(log_path=log_path, logger_name="dedupe_test")
    before_count = len(logger.handlers)

    same_logger = get_file_logger(log_path=log_path, logger_name="dedupe_test")
    after_count = len(same_logger.handlers)

    assert before_count == after_count
