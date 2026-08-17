import { RecordListPage } from "@/components/RecordListPage";

export default function DecisionsPage() {
  return (
    <RecordListPage
      title="Beslutninger"
      description="Beslutninger du følger opp."
      path="/decisions/"
      fields={["title", "status", "created_at"]}
    />
  );
}
