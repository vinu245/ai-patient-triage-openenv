export default function QueueList({ queue }) {
  return (
    <section className="glass rounded-2xl p-5">
      <h3 className="font-display text-base font-semibold text-slate-100">Patient Queue</h3>
      <div className="scroll-slim mt-4 max-h-72 space-y-2 overflow-auto pr-1">
        {queue.length === 0 ? (
          <p className="text-sm text-slate-400">Queue is currently empty.</p>
        ) : (
          queue.slice(0, 20).map((item) => (
            <div
              key={item.patient_id}
              className="rounded-xl border border-slate-700/70 bg-slate-900/45 p-3 text-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-100">{item.patient_id}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    item.task_level === "hard"
                      ? "bg-coral/20 text-coral"
                      : item.task_level === "medium"
                        ? "bg-amber/20 text-amber"
                        : "bg-sky/20 text-sky"
                  }`}
                >
                  {item.task_level}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-300">{item.symptoms.join(", ")}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
