"""Classify uploaded documents and suggest asset links / updates."""

from __future__ import annotations

import re

from app.services.storage_service import list_records

_DOC_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "insurance": ("forsikring", "polise", "forsikringsbevis", "insurance", "policy"),
    "invoice": ("faktura", "invoice", "kvittering", "receipt", "beløp", "sum"),
    "contract": ("kontrakt", "contract", "avtale", "kjøpekontrakt", "leiekontrakt"),
    "service": ("service", "verksted", "reparasjon", "vedlikehold", "inspeksjon", "eu-kontroll"),
    "warranty": ("garanti", "warranty", "reklamasjon"),
}


def _normalize(text: str) -> str:
    return (text or "").lower()


def classify_document(filename: str, text_content: str | None) -> str:
    """Return document type from filename and extracted text."""
    haystack = _normalize(f"{filename} {text_content or ''}")
    best_type = "other"
    best_score = 0
    for doc_type, keywords in _DOC_TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_score = score
            best_type = doc_type
    return best_type if best_score > 0 else "other"


def _match_asset_name(text: str, assets: list[dict]) -> dict | None:
    lowered = _normalize(text)
    for asset in assets:
        name = _normalize(asset.get("name") or "")
        if len(name) >= 3 and name in lowered:
            return asset
    return None


def _match_asset_from_tokens(text: str, assets: list[dict]) -> dict | None:
    tokens = set(re.findall(r"[a-zæøå0-9]{3,}", _normalize(text)))
    best_asset = None
    best_score = 0
    for asset in assets:
        name = asset.get("name") or ""
        name_tokens = set(re.findall(r"[a-zæøå0-9]{3,}", _normalize(name)))
        overlap = len(tokens & name_tokens)
        if overlap > best_score:
            best_score = overlap
            best_asset = asset
    return best_asset if best_score > 0 else None


def suggest_asset_link(
    filename: str,
    text_content: str | None,
    *,
    asset_id: str | None = None,
) -> str | None:
    if asset_id:
        return asset_id
    assets = list_records("assets")
    if not assets:
        return None
    haystack = f"{filename} {text_content or ''}"
    matched = _match_asset_name(haystack, assets) or _match_asset_from_tokens(haystack, assets)
    return matched["id"] if matched else None


def build_upload_suggestions(
    *,
    filename: str,
    text_content: str | None,
    doc_type: str,
    asset_id: str | None,
    suggested_asset_id: str | None,
) -> list[dict]:
    """Return UI-ready suggestions for Accept / Ignore flows."""
    suggestions: list[dict] = []
    assets = {asset["id"]: asset for asset in list_records("assets")}
    target_asset_id = asset_id or suggested_asset_id
    target_asset = assets.get(target_asset_id) if target_asset_id else None

    if not asset_id and suggested_asset_id and target_asset:
        suggestions.append(
            {
                "id": "link_asset",
                "type": "link_asset",
                "label": "Koble til eiendel",
                "message": f"Koble «{filename}» til {target_asset['name']}?",
                "payload": {"asset_id": suggested_asset_id},
            }
        )

    if doc_type == "insurance" and target_asset:
        suggestions.append(
            {
                "id": "update_insurance",
                "type": "update_asset",
                "label": "Oppdater forsikring",
                "message": f"Ny forsikring for {target_asset['name']}? Oppdater eiendelsinformasjon.",
                "payload": {
                    "asset_id": target_asset["id"],
                    "hint": "insurance",
                    "doc_type": doc_type,
                },
            }
        )
    elif doc_type == "service" and target_asset:
        suggestions.append(
            {
                "id": "create_service_task",
                "type": "create_task",
                "label": "Opprett service-oppgave",
                "message": f"Opprett oppfølgingsoppgave for {target_asset['name']}?",
                "payload": {
                    "title": f"Service: {target_asset['name']}",
                    "asset_id": target_asset["id"],
                    "priority": 2,
                    "status": "open",
                },
            }
        )

    return suggestions


def analyze_uploaded_document(
    filename: str,
    text_content: str | None,
    *,
    asset_id: str | None = None,
) -> dict:
    doc_type = classify_document(filename, text_content)
    suggested_asset_id = suggest_asset_link(filename, text_content, asset_id=asset_id)
    suggestions = build_upload_suggestions(
        filename=filename,
        text_content=text_content,
        doc_type=doc_type,
        asset_id=asset_id,
        suggested_asset_id=suggested_asset_id,
    )
    return {
        "doc_type": doc_type,
        "suggested_asset_id": suggested_asset_id,
        "suggestions": suggestions,
    }


def analyze_stored_document(document: dict) -> dict:
    """Re-run intelligence for an existing document record."""
    from app.services.document_storage import read_document_text

    text_content = document.get("text_content")
    storage_path = document.get("storage_path")
    filename = document.get("filename") or "document"
    if not text_content and storage_path:
        text_content = read_document_text(str(storage_path), filename)
    return analyze_uploaded_document(
        filename,
        text_content,
        asset_id=document.get("asset_id"),
    )
