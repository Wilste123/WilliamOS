export type HomeSummary = {
  greeting_name: string;
  net_worth_nok: number;
  net_worth_formatted: string;
  active_goals: number;
  open_tasks: number;
  priorities: string[];
  metrics?: {
    projects: number;
  };
};

export function getTimeGreeting(name: string): string {
  const hour = new Date().getHours();
  if (hour < 10) return `God morgen ${name}`;
  if (hour < 17) return `God dag ${name}`;
  return `God kveld ${name}`;
}
