import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
AUDIT_LOG_FILE = LOG_DIR / "audit.jsonl"


def _ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    if not SUBMISSIONS_FILE.exists():
        SUBMISSIONS_FILE.write_text("{}", encoding="utf-8")
    if not AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.write_text("", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_submissions() -> dict[str, Any]:
    _ensure_storage()
    return json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8"))


def _write_submissions(payload: dict[str, Any]) -> None:
    _ensure_storage()
    SUBMISSIONS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_audit_entry(entry: dict[str, Any]) -> None:
    _ensure_storage()
    with AUDIT_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def save_submission(record: dict[str, Any]) -> None:
    submissions = _read_submissions()
    submissions[record["content_id"]] = record
    _write_submissions(submissions)


def get_submission(content_id: str) -> dict[str, Any] | None:
    submissions = _read_submissions()
    return submissions.get(content_id)


def create_submission_record(content_id: str, creator_id: str, text: str, decision: dict[str, Any], label: str) -> dict[str, Any]:
    return {
        "content_id": content_id,
        "creator_id": creator_id,
        "text": text,
        "status": "classified",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "attribution": decision["attribution"],
        "confidence": decision["confidence"],
        "label": label,
        "llm_score": decision["signals"]["llm"]["score"],
        "stylometric_score": decision["signals"]["stylometric"]["score"],
        "appeal_reasoning": None,
    }


def record_submission_event(record: dict[str, Any], decision: dict[str, Any]) -> None:
    append_audit_entry(
        {
            "event_type": "submission",
            "timestamp": _utc_now(),
            "content_id": record["content_id"],
            "creator_id": record["creator_id"],
            "status": record["status"],
            "attribution": record["attribution"],
            "confidence": record["confidence"],
            "llm_score": decision["signals"]["llm"]["score"],
            "llm_reason": decision["signals"]["llm"]["reason"],
            "stylometric_score": decision["signals"]["stylometric"]["score"],
            "stylometric_features": decision["signals"]["stylometric"].get("features", {}),
        }
    )


def submit_appeal(content_id: str, creator_reasoning: str) -> dict[str, Any] | None:
    submissions = _read_submissions()
    record = submissions.get(content_id)
    if record is None:
        return None

    record["status"] = "under_review"
    record["updated_at"] = _utc_now()
    record["appeal_reasoning"] = creator_reasoning
    submissions[content_id] = record
    _write_submissions(submissions)

    append_audit_entry(
        {
            "event_type": "appeal",
            "timestamp": _utc_now(),
            "content_id": content_id,
            "creator_id": record["creator_id"],
            "status": record["status"],
            "attribution": record["attribution"],
            "confidence": record["confidence"],
            "llm_score": record["llm_score"],
            "stylometric_score": record["stylometric_score"],
            "appeal_reasoning": creator_reasoning,
        }
    )
    return record


def get_recent_audit_entries(limit: int = 25) -> list[dict[str, Any]]:
    _ensure_storage()
    lines = [line for line in AUDIT_LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]
    return entries[-limit:]
