import { RecordListPage } from "@/components/RecordListPage";

export default function EventsPage() {
  return (
    <RecordListPage
      title="Hendelser"
      description="Hendelser og milepæler."
      path="/events/"
      fields={["title", "event_type", "event_date"]}
    />
  );
}
