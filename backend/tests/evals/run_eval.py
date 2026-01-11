"""Eval harness for groundedness, citation accuracy, and refusal rate."""
from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import psycopg2


DATA_PATH = Path(__file__).parent / "golden_data.json"
API_BASE_URL = os.getenv("EVAL_API_BASE_URL", "http://localhost:3000")


@dataclass
class EvalResult:
    id: str
    answerable: bool
    grounded: bool
    citation_accurate: bool
    refused: bool
    error: str | None = None
    retrieval_status: str | None = None
    retrieval_results: int | None = None


def _db_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "rag_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


def _sample_chunks(filename: str, limit: int = 5) -> List[str]:
    conn = psycopg2.connect(**_db_config())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.content
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.filename = %s
                ORDER BY random()
                LIMIT %s
                """,
                (filename, limit),
            )
            rows = cur.fetchall()
            return [r[0] for r in rows]
    finally:
        conn.close()


def _make_answerable_qas(filename: str, count: int = 5) -> List[Dict[str, Any]]:
    chunks = _sample_chunks(filename, limit=count)
    qas: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks, 1):
        words = [w for w in chunk.split() if len(w) > 2]
        if len(words) < 10:
            continue
        start = random.randint(0, max(0, len(words) - 10))
        phrase_words = words[start : start + 6]
        phrase = " ".join(phrase_words)
        qas.append(
            {
                "id": f"auto_{idx}",
                "question": (
                    "In the document, there is a text snippet containing the phrase "
                    f'"{phrase}". Repeat that snippet verbatim.'
                ),
                "answerable": True,
                "document_filename": filename,
                "expected_terms": phrase_words[:3],
            }
        )
    return qas


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in text.split(".") if len(s.strip()) > 10]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _groundedness(answer: str, chunks: List[Dict[str, Any]], expected_terms: Optional[List[str]] = None) -> bool:
    if not answer or not chunks:
        return False
    if expected_terms:
        normalized = _normalize(" ".join(c.get("content", "") for c in chunks))
        return all(_normalize(term) in normalized for term in expected_terms)
    chunk_text = _normalize(" ".join(c.get("content", "") for c in chunks))
    for sentence in _split_sentences(answer):
        snippet = _normalize(sentence)
        if len(snippet) >= 30 and snippet in chunk_text:
            return True
    # Fallback: check for any 2 expected noun phrases (very light heuristic)
    return False


def _citation_accuracy(citations: List[Dict[str, Any]], expected_terms: Optional[List[str]] = None) -> bool:
    if not citations:
        return False
    for citation in citations:
        source_chunks = citation.get("source_chunks", [])
        if not source_chunks:
            return False
        if expected_terms:
            if not any(
                all(_normalize(term) in _normalize(c.get("content", "")) for term in expected_terms)
                for c in source_chunks
            ):
                return False
        else:
            statement = _normalize(citation.get("statement", ""))
            if not statement:
                return False
            if not any(statement in _normalize(c.get("content", "")) for c in source_chunks):
                return False
    return True


def _is_refusal(response: Dict[str, Any]) -> bool:
    final_text = (response.get("final_text") or "").lower()
    return "i don't know" in final_text or "cannot answer" in final_text


def run_eval(document_filename: Optional[str] = None) -> Dict[str, Any]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if document_filename:
        answerable = _make_answerable_qas(document_filename, count=5)
        unanswerable = [item for item in data if not item.get("answerable")][:5]
        data = answerable + unanswerable
    results: List[EvalResult] = []

    with httpx.Client(timeout=60.0) as client:
        for item in data:
            payload: Dict[str, Any] = {
                "query": item["question"],
                "top_k": 5,
                "similarity_threshold": -1.0,
            }
            if item.get("document_filename"):
                payload["document_filename"] = item["document_filename"]
            try:
                retrieval_count = None
                retrieval_status = None
                try:
                    r_resp = client.post(f"{API_BASE_URL}/api/v1/retrieve", json=payload)
                    if r_resp.status_code == 200:
                        r_body = r_resp.json()
                        retrieval_count = r_body.get("result_count")
                except Exception:
                    retrieval_count = None

                resp = client.post(f"{API_BASE_URL}/chat", json=payload)
                resp.raise_for_status()
                body = resp.json()
                response = body.get("response", {})
                retrieval_status = body.get("retrieval_status")
                refused = _is_refusal(response)
                expected_terms = item.get("expected_terms")
                grounded = _groundedness(response.get("final_text", ""), response.get("citations", []), expected_terms)
                citation_accurate = _citation_accuracy(response.get("citations", []), expected_terms)
                results.append(
                    EvalResult(
                        id=item["id"],
                        answerable=item["answerable"],
                        grounded=grounded,
                        citation_accurate=citation_accurate,
                        refused=refused,
                        retrieval_status=retrieval_status,
                        retrieval_results=retrieval_count,
                    )
                )
            except Exception as exc:
                results.append(
                    EvalResult(
                        id=item["id"],
                        answerable=item["answerable"],
                        grounded=False,
                        citation_accurate=False,
                        refused=False,
                        error=str(exc),
                        retrieval_status=None,
                        retrieval_results=None,
                    )
                )

    total = len(results)
    grounded_score = sum(1 for r in results if r.answerable and r.grounded)
    citation_score = sum(1 for r in results if r.answerable and r.citation_accurate)
    refusal_score = sum(1 for r in results if not r.answerable and r.refused)

    report = {
        "total": total,
        "groundedness": grounded_score / max(1, sum(1 for r in results if r.answerable)),
        "citation_accuracy": citation_score / max(1, sum(1 for r in results if r.answerable)),
        "refusal_rate": refusal_score / max(1, sum(1 for r in results if not r.answerable)),
        "results": [r.__dict__ for r in results],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", dest="document_filename", help="Filename to scope answerable evals")
    args = parser.parse_args()
    report = run_eval(args.document_filename)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
