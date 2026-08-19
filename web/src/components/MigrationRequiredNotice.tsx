type MigrationRequiredNoticeProps = {
  migrationFile: string;
};

export function MigrationRequiredNotice({ migrationFile }: MigrationRequiredNoticeProps) {
  return (
    <p className="break-words text-sm text-red-400">
      Kunne ikke laste data. Kjør migrasjonen{" "}
      <code className="break-all text-xs">{migrationFile}</code> i Supabase.
    </p>
  );
}
