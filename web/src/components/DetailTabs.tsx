type DetailTab<T extends string> = {
  id: T;
  label: string;
};

type DetailTabsProps<T extends string> = {
  tabs: DetailTab<T>[];
  active: T;
  onChange: (tab: T) => void;
};

export function DetailTabs<T extends string>({ tabs, active, onChange }: DetailTabsProps<T>) {
  return (
    <div className="-mx-4 flex gap-2 overflow-x-auto px-4">
      {tabs.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChange(item.id)}
          className={`shrink-0 rounded-full px-4 py-2 text-sm ${
            active === item.id
              ? "bg-accent text-white"
              : "border border-border text-muted hover:text-foreground"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
