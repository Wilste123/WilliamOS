import { RecordListPage } from "@/components/RecordListPage";

export default function TasksPage() {
  return (
    <RecordListPage
      title="Oppgaver"
      description="Alle oppgaver i systemet."
      path="/tasks/"
      fields={["title", "priority", "due_date", "status"]}
    />
  );
}
