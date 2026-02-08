from utils.csv_helper import save_titles_to_csv


def test_save_titles_to_csv(tmp_path):
    output = tmp_path / "titles.csv"
    records = [
        "First Paper",
        {"title": "Second Paper"},
        {"title": "   Third Paper   "},
        {"title": ""},
        {"name": "ignored"},
    ]

    path = save_titles_to_csv(records, output)

    assert path == output
    assert output.read_text(encoding="utf-8") == (
        "column_number,title\n"
        "0,First Paper\n"
        "1,Second Paper\n"
        "2,Third Paper\n"
    )
