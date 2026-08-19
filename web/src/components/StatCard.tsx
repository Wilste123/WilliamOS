import Link from "next/link";

type StatCardProps = {
  label: string;
  value: string;
  hint?: string;
  href?: string;
};

export function StatCard({ label, value, hint, href }: StatCardProps) {
  const card = (
    <div className="rounded-2xl border border-border bg-zinc-950/50 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 break-words text-2xl font-semibold">{value}</p>
      {hint && !href ? <p className="mt-1 break-words text-xs text-muted">{hint}</p> : null}
      {hint && href ? (
        <span className="mt-2 inline-block text-sm text-accent">{hint}</span>
      ) : null}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block transition hover:border-accent/40">
        {card}
      </Link>
    );
  }

  return card;
}
