"use client";

import { FormEvent, useEffect, useState } from "react";

import { CreateRecordForm } from "@/components/CreateRecordForm";
import { VisibilitySelect } from "@/components/VisibilitySelect";
import { createGoal, fetchCollection } from "@/lib/api";
import { GOAL_MODULES, goalModuleNeedsLink, type GoalModule } from "@/lib/goal-modules";
import { entityRecordLabel } from "@/lib/project-links";
import type { Visibility } from "@/lib/visibility";

type GoalCreateSectionProps = {
  onCreated?: () => void;
};

const LINK_FETCHERS: Partial<Record<GoalModule, () => Promise<Record<string, unknown>[]>>> = {
  asset: () => fetchCollection("/assets"),
  project: () => fetchCollection("/projects"),
  finance: () => fetchCollection("/finance/accounts").catch(() => []),
};

export function GoalCreateSection({ onCreated }: GoalCreateSectionProps) {
  const [module, setModule] = useState<GoalModule>("general");
  const [linkedId, setLinkedId] = useState("");
  const [options, setOptions] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (!goalModuleNeedsLink(module)) {
      setOptions([]);
      setLinkedId("");
      return;
    }
    const loader = LINK_FETCHERS[module];
    if (!loader) return;
    loader().then(setOptions).catch(() => setOptions([]));
  }, [module]);

  if (module !== "general") {
    return (
      <div className="space-y-3 rounded-2xl border border-border p-4">
        <ModuleSelect value={module} onChange={setModule} />

        {goalModuleNeedsLink(module) && (
          <label className="block space-y-1 text-sm">
            <span>Knytt til</span>
            <select
              value={linkedId}
              onChange={(e) => setLinkedId(e.target.value)}
              className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
            >
              <option value="">Velg record…</option>
              {options.map((option) => (
                <option key={String(option.id)} value={String(option.id)}>
                  {entityRecordLabel(option)}
                </option>
              ))}
            </select>
          </label>
        )}

        <InlineGoalForm
          onSubmit={async (body) => {
            await createGoal({
              ...body,
              module,
              linked_id: goalModuleNeedsLink(module) && linkedId ? linkedId : null,
            });
            onCreated?.();
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <ModuleSelect value={module} onChange={setModule} />
      <CreateRecordForm
        path="/goals"
        submitLabel="Opprett mål"
        showVisibility
        fields={[
          { name: "title", label: "Tittel", type: "text", required: true, placeholder: "Hva vil du oppnå?" },
          { name: "next_step", label: "Neste steg", type: "text", placeholder: "Neste handling" },
          { name: "target_date", label: "Måldato", type: "date" },
        ]}
        onCreated={() => onCreated?.()}
      />
    </div>
  );
}

function ModuleSelect({
  value,
  onChange,
}: {
  value: GoalModule;
  onChange: (value: GoalModule) => void;
}) {
  return (
    <label className="block space-y-1 text-sm">
      <span>Modul</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as GoalModule)}
        className="w-full rounded-xl border border-border bg-transparent px-4 py-3"
      >
        {GOAL_MODULES.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function InlineGoalForm({ onSubmit }: { onSubmit: (body: Record<string, unknown>) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("household");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = { title: title.trim(), visibility };
      if (nextStep.trim()) body.next_step = nextStep.trim();
      if (targetDate) body.target_date = targetDate;
      await onSubmit(body);
      setTitle("");
      setNextStep("");
      setTargetDate("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Hva vil du oppnå?"
        required
        className="w-full rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
      />
      <input
        value={nextStep}
        onChange={(e) => setNextStep(e.target.value)}
        placeholder="Neste steg"
        className="w-full rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
      />
      <input
        type="date"
        value={targetDate}
        onChange={(e) => setTargetDate(e.target.value)}
        className="w-full rounded-xl border border-border bg-transparent px-4 py-3 text-sm"
      />
      <VisibilitySelect value={visibility} onChange={setVisibility} />
      <button
        type="submit"
        disabled={submitting}
        className="rounded-xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        Opprett mål
      </button>
    </form>
  );
}
