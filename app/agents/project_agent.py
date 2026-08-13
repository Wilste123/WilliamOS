def summarize_project(project: dict, tasks: list[dict] | None = None) -> str:
    tasks = tasks or []
    open_tasks = [t for t in tasks if not t.get('completed')]
    return (
        f"Prosjekt: {project.get('name')}\n"
        f"Status: {project.get('status')}\n"
        f"Neste steg: {project.get('next_action') or 'Ikke satt'}\n"
        f"Åpne oppgaver: {len(open_tasks)}"
    )
