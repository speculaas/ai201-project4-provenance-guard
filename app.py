import os
import uuid

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from audit import (
    create_submission_record,
    get_recent_audit_entries,
    record_submission_event,
    save_submission,
    submit_appeal,
)
from detector import llm_authorship_signal, stylometric_signal
from labels import label_for_attribution
from scoring import build_decision

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.get("/")
def index():
    return jsonify(
        {
            "message": "Provenance Guard API",
            "endpoints": ["POST /submit", "POST /appeal", "GET /log"],
        }
    )


@app.post("/submit")
@limiter.limit("10 per minute;100 per day")
def submit():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    creator_id = (payload.get("creator_id") or "").strip()

    if not text or not creator_id:
        return jsonify({"error": "Both text and creator_id are required."}), 400

    content_id = str(uuid.uuid4())

    llm_signal = llm_authorship_signal(text)
    style_signal = stylometric_signal(text)
    decision = build_decision(llm_signal, style_signal)
    label = label_for_attribution(decision["attribution"])

    record = create_submission_record(
        content_id=content_id,
        creator_id=creator_id,
        text=text,
        decision=decision,
        label=label,
    )
    save_submission(record)
    record_submission_event(record, decision)

    return jsonify(
        {
            "content_id": content_id,
            "status": record["status"],
            "attribution": decision["attribution"],
            "confidence": decision["confidence"],
            "label": label,
            "signals": {
                "llm_score": decision["signals"]["llm"]["score"],
                "llm_reason": decision["signals"]["llm"]["reason"],
                "stylometric_score": decision["signals"]["stylometric"]["score"],
                "stylometric_features": decision["signals"]["stylometric"].get("features", {}),
            },
        }
    )


@app.post("/appeal")
def appeal():
    payload = request.get_json(silent=True) or {}
    content_id = (payload.get("content_id") or "").strip()
    creator_reasoning = (payload.get("creator_reasoning") or "").strip()

    if not content_id or not creator_reasoning:
        return jsonify({"error": "Both content_id and creator_reasoning are required."}), 400

    updated = submit_appeal(content_id, creator_reasoning)
    if updated is None:
        return jsonify({"error": "content_id not found"}), 404

    return jsonify(
        {
            "message": "Appeal received and marked for review.",
            "content_id": content_id,
            "status": updated["status"],
            "appeal_reasoning": updated["appeal_reasoning"],
        }
    )


@app.get("/log")
def log_view():
    return jsonify({"entries": get_recent_audit_entries()})


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"Provenance Guard listening on http://{host}:{port}")
    app.run(debug=True, host=host, port=port)
