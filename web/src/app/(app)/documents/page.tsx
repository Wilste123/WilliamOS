import { RecordListPage } from "@/components/RecordListPage";

export default function DocumentsPage() {
  return (
    <RecordListPage
      title="Dokumenter"
      description="Opplastede dokumenter og filer."
      path="/documents/"
      fields={["filename", "source_module", "created_at"]}
    />
  );
}
