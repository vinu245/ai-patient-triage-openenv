export default function StatCard({ title, value, accent, icon: Icon, subtitle }) {
  return (
    <div className="glass rounded-2xl p-4 animate-floatIn">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">{title}</p>
          <p className={`mt-2 text-2xl font-bold ${accent}`}>{value}</p>
          <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
        </div>
        <div className="rounded-lg border border-slate-600 bg-slate-900/50 p-2">
          <Icon className="h-4 w-4 text-slate-200" />
        </div>
      </div>
    </div>
  );
}
