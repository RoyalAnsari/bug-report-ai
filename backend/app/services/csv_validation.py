import csv
import io

ALLOWED_SEVERITIES = ("blocker", "critical", "major", "normal", "minor", "trivial")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50_000
MIN_TEXT_LENGTH = 3
MAX_TEXT_LENGTH = 2000
MAX_REPORTED_ERRORS = 100

FIELD_CANDIDATES = {
    "text": ["short description", "summary", "title", "description", "text"],
    "severity": ["severity label", "severity"],
    "project": ["project", "product", "component"],
    "external_id": ["bug id", "issue id", "id"],
}


class CsvValidationError(ValueError):
    """Poori file ka masla (galat type, bohat bari, header nahi, wagaira)."""


def decode_bytes(data):
    try:
        return data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("latin-1"), "latin-1"


def read_csv_rows(data, filename, max_bytes=MAX_FILE_BYTES, max_rows=MAX_ROWS):
    """File ki type, size, header aur rows ki ginti check karta hai."""
    if not str(filename).lower().endswith(".csv"):
        raise CsvValidationError("Only .csv files are accepted")
    if len(data) == 0:
        raise CsvValidationError("File is empty")
    if len(data) > max_bytes:
        raise CsvValidationError(f"File is too large (limit is {max_bytes} bytes)")

    content, encoding = decode_bytes(data)
    try:
        reader = csv.reader(io.StringIO(content, newline=""))
        headers = next(reader, None)
        if not headers or not any(h.strip() for h in headers):
            raise CsvValidationError("File has no header row")
        headers = [h.strip() for h in headers]
        if len({h.lower() for h in headers}) != len(headers):
            raise CsvValidationError("File has duplicate column names")

        rows = []
        for values in reader:
            if not any(v.strip() for v in values):
                continue  # khali lines chhor dete hain
            if len(rows) >= max_rows:
                raise CsvValidationError(f"File has more than {max_rows} rows")
            rows.append(dict(zip(headers, values)))
    except csv.Error as error:
        raise CsvValidationError(f"Could not parse CSV: {error}") from error
    return headers, rows, encoding


def suggest_mapping(headers):
    """Column ke naam dekh kar andaaza lagata hai ke kaun sa column kya hai."""
    lookup = {h.strip().lower(): h for h in headers}
    mapping = {}
    for field_name, candidates in FIELD_CANDIDATES.items():
        mapping[field_name] = next((lookup[c] for c in candidates if c in lookup), None)
    return mapping


def _cell(row, column, limit):
    if not column:
        return None
    value = " ".join(str(row.get(column) or "").split())[:limit]
    return value or None


def validate_rows(headers, rows, mapping):
    """Har row jaanchta hai. Row number data rows ka hai (header ginti mein nahi)."""
    if not mapping.get("text"):
        raise CsvValidationError("Choose which column holds the bug text")
    for field_name, column in mapping.items():
        if column and column not in headers:
            raise CsvValidationError(f"Column '{column}' (for {field_name}) was not found in the file")

    valid, errors, error_count = [], [], 0
    for number, row in enumerate(rows, start=1):
        problems = []
        text = " ".join(str(row.get(mapping["text"]) or "").split())
        if not text:
            problems.append("Text is empty")
        elif len(text) < MIN_TEXT_LENGTH:
            problems.append(f"Text is shorter than {MIN_TEXT_LENGTH} characters")
        elif len(text) > MAX_TEXT_LENGTH:
            problems.append(f"Text is longer than {MAX_TEXT_LENGTH} characters")

        severity = None
        if mapping.get("severity"):
            raw = str(row.get(mapping["severity"]) or "").strip().lower()
            if raw in ALLOWED_SEVERITIES:
                severity = raw
            elif raw:
                problems.append(f"Unknown severity '{raw[:30]}'")

        if problems:
            error_count += 1
            if len(errors) < MAX_REPORTED_ERRORS:
                errors.append({"row": number, "message": "; ".join(problems)})
            continue

        valid.append(
            {
                "text": text,
                "severity": severity,
                "project": _cell(row, mapping.get("project"), 100),
                "external_id": _cell(row, mapping.get("external_id"), 100),
            }
        )

    return {
        "total_rows": len(rows),
        "valid_rows": len(valid),
        "error_count": error_count,
        "errors": errors,
        "errors_truncated": error_count > len(errors),
        "valid": valid,
    }


def parse_upload(data, filename, mapping=None):
    """Upload ki poori jaanch: file, columns ka mapping, preview aur row errors."""
    headers, rows, encoding = read_csv_rows(data, filename)
    used = mapping or suggest_mapping(headers)
    result = validate_rows(headers, rows, used)
    return {"encoding": encoding, "headers": headers, "mapping": used, "preview": rows[:5], **result}