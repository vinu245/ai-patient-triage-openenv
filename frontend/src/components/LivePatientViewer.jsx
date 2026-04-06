export default function LivePatientViewer({ patient }) {
  return (
    <section className="glass rounded-2xl p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-base font-semibold text-slate-100">Live Patient Viewer</h3>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
          {patient ? patient.patient_id : "No active patient"}
        </span>
      </div>

      {!patient ? (
        <p className="text-sm text-slate-400">Run a step to process the next patient.</p>
      ) : (
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-xl border border-slate-700/70 bg-slate-900/50 p-3">
            <p className="text-xs uppercase tracking-wider text-slate-400">Symptoms</p>
            <p className="mt-1 text-slate-100">{patient.symptoms.join(", ")}</p>
          </div>
          <div className="rounded-xl border border-slate-700/70 bg-slate-900/50 p-3">
            <p className="text-xs uppercase tracking-wider text-slate-400">History</p>
            <p className="mt-1 text-slate-100">{patient.history.join(", ")}</p>
          </div>
          <div className="rounded-xl border border-slate-700/70 bg-slate-900/50 p-3">
            <p className="text-xs uppercase tracking-wider text-slate-400">Allergies</p>
            <p className="mt-1 text-slate-100">{patient.allergies.join(", ")}</p>
          </div>
          <div className="rounded-xl border border-slate-700/70 bg-slate-900/50 p-3">
            <p className="text-xs uppercase tracking-wider text-slate-400">Vitals</p>
            <p className="mt-1 text-slate-100">
              HR {patient.vitals.heart_rate} | SpO2 {patient.vitals.oxygen}% | Temp {patient.vitals.temperature}F
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
