import { RecordListPage } from "@/components/RecordListPage";

export default function ProjectsPage() {
  return (
    <RecordListPage
      title="Prosjekter"
      description="Aktive og avsluttede prosjekter."
      path="/projects/"
      fields={["name", "status", "next_action"]}
    />
  );
}
