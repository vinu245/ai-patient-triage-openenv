export default function DecisionLogs({ logs }) {
  return (
    <section className="glass rounded-2xl p-5">
      <h3 className="font-display text-base font-semibold text-slate-100">Agent Decision Logs</h3>
      <div className="scroll-slim mt-4 max-h-72 space-y-2 overflow-auto pr-1">
        {logs.length === 0 ? (
          <p className="text-sm text-slate-400">No decisions yet.</p>
        ) : (
          logs.map((entry, idx) => (
            <div
              key={`${entry.agent}-${idx}`}
              className="rounded-xl border border-slate-700/70 bg-slate-900/50 p-3"
            >
              <p className="text-xs uppercase tracking-wide text-slate-400">{entry.agent}</p>
              <p className="mt-1 text-sm text-slate-100">{entry.rationale}</p>
              {entry.action && (
                <p className="mt-1 text-xs text-slate-300">
                  triage={entry.action.triage_level}, dept={entry.action.department}, priority={entry.action.priority}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
