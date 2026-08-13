def summarize_asset(asset: dict, documents: list[dict] | None = None, tasks: list[dict] | None = None) -> str:
    documents = documents or []
    tasks = tasks or []
    return (
        f"Asset: {asset.get('name')}\n"
        f"Type: {asset.get('type')}\n"
        f"Description: {asset.get('description', '')}\n"
        f"Documents: {len(documents)}\n"
        f"Open tasks: {len([t for t in tasks if not t.get('completed')])}"
    )
