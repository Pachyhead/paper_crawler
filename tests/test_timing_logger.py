import time

from utils.timing_logger import log_execution_time


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
