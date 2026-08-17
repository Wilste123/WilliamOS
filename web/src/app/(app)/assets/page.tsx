import { RecordListPage } from "@/components/RecordListPage";

export default function AssetsPage() {
  return (
    <RecordListPage
      title="Eiendeler"
      description="Boliger, kjøretøy, båter og andre eiendeler."
      path="/assets/"
      fields={["name", "type", "status", "estimated_value"]}
    />
  );
}
