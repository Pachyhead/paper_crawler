import time

from utils.timing_logger import log_execution_time


def test_log_execution_time_writes_file(tmp_path):
    log_path = tmp_path / "logs" / "execution.log"

    with log_execution_time("sample_block", log_path=log_path):
        time.sleep(0.01)

    content = log_path.read_text(encoding="utf-8")
    assert "sample_block completed in" in content
