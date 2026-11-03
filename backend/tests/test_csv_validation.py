import pytest

from app.services.csv_validation import (
    CsvValidationError,
    parse_upload,
    read_csv_rows,
    suggest_mapping,
    validate_rows,
)

GOOD = b"Bug ID,Severity Label,Short Description,Project\n1,major,Crash on save,Core\n2,minor,Typo in menu,JDT\n"


def test_suggest_mapping_for_dataset_columns():
    headers = ["Project", "Bug ID", "Severity Label", "Resolution Status", "Short Description"]
    assert suggest_mapping(headers) == {
        "text": "Short Description",
        "severity": "Severity Label",
        "project": "Project",
        "external_id": "Bug ID",
    }


def test_valid_file_is_parsed():
    result = parse_upload(GOOD, "bugs.csv")
    assert result["valid_rows"] == 2
    assert result["error_count"] == 0
    assert result["valid"][0] == {
        "text": "Crash on save",
        "severity": "major",
        "project": "Core",
        "external_id": "1",
    }
    assert len(result["preview"]) == 2


def test_rejects_non_csv_extension():
    with pytest.raises(CsvValidationError):
        parse_upload(GOOD, "bugs.xlsx")


def test_rejects_empty_file():
    with pytest.raises(CsvValidationError):
        parse_upload(b"", "bugs.csv")


def test_rejects_too_large_file():
    with pytest.raises(CsvValidationError):
        read_csv_rows(GOOD, "bugs.csv", max_bytes=10)


def test_rejects_too_many_rows():
    with pytest.raises(CsvValidationError):
        read_csv_rows(GOOD, "bugs.csv", max_rows=1)


def test_rejects_duplicate_headers():
    with pytest.raises(CsvValidationError):
        read_csv_rows(b"a,a\n1,2\n", "bugs.csv")


def test_requires_text_column_in_mapping():
    with pytest.raises(CsvValidationError):
        validate_rows(["a"], [], {"text": None})
    with pytest.raises(CsvValidationError):
        validate_rows(["a"], [], {"text": "missing"})


def test_bad_rows_are_reported_with_row_numbers():
    data = b"Short Description,Severity Label\nok text here,major\nx,major\nlong enough,urgent\n"
    result = parse_upload(data, "bugs.csv")
    assert result["valid_rows"] == 1
    assert result["error_count"] == 2
    assert [e["row"] for e in result["errors"]] == [2, 3]


def test_blank_severity_is_allowed():
    data = b"Short Description,Severity Label\nsome report text,\n"
    result = parse_upload(data, "bugs.csv")
    assert result["valid_rows"] == 1
    assert result["valid"][0]["severity"] is None


def test_latin1_file_is_decoded():
    data = b"Short Description\nCaf\xe9 crash here\n"
    result = parse_upload(data, "bugs.csv")
    assert result["encoding"] == "latin-1"
    assert result["valid_rows"] == 1


def test_error_list_is_capped():
    lines = b"Short Description\n" + b"x\n" * 150
    result = parse_upload(lines, "bugs.csv")
    assert result["error_count"] == 150
    assert len(result["errors"]) == 100
    assert result["errors_truncated"] is True