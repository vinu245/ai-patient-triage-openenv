import { Activity, Gauge, PlayCircle, RefreshCw, Stethoscope, Timer } from "lucide-react";

const nav = [
  { label: "Triage Control", icon: Activity },
  { label: "Routing Monitor", icon: Stethoscope },
  { label: "Performance", icon: Gauge },
  { label: "Latency", icon: Timer },
];

export default function Sidebar({ running, onRunStep, onReset, autoRun, onToggleAuto }) {
  return (
    <aside className="glass rounded-2xl p-5 animate-floatIn">
      <div className="mb-6">
        <p className="font-display text-lg font-semibold text-glow">CareFlow AI</p>
        <p className="text-xs text-slate-300">Patient Triage & Routing</p>
      </div>

      <div className="space-y-2">
        {nav.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="flex items-center gap-3 rounded-xl border border-slate-700/60 bg-slate-900/45 px-3 py-2 text-sm text-slate-200"
            >
              <Icon className="h-4 w-4 text-sky" />
              <span>{item.label}</span>
            </div>
          );
        })}
      </div>

      <div className="mt-8 space-y-3">
        <button
          onClick={onRunStep}
          disabled={running}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-glow to-sky px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <PlayCircle className="h-4 w-4" />
          Run Single Step
        </button>

        <button
          onClick={onToggleAuto}
          className={`w-full rounded-xl px-4 py-2 text-sm font-semibold transition ${
            autoRun
              ? "bg-amber text-slate-950 hover:brightness-110"
              : "bg-slate-700 text-slate-100 hover:bg-slate-600"
          }`}
        >
          {autoRun ? "Stop Auto-Run" : "Start Auto-Run"}
        </button>

        <button
          onClick={onReset}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-500 bg-slate-900/65 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:border-coral hover:text-coral"
        >
          <RefreshCw className="h-4 w-4" />
          Reset Environment
        </button>
      </div>
    </aside>
  );
}
