import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function buildSeries(metrics) {
  const len = Math.max(
    metrics.reward_history.length,
    metrics.accuracy_history.length,
    metrics.patient_load_history.length
  );

  return Array.from({ length: len }, (_, i) => ({
    tick: i + 1,
    reward: metrics.reward_history[i] ?? null,
    accuracy: metrics.accuracy_history[i] ?? null,
    load: metrics.patient_load_history[i] ?? null,
  }));
}

export default function MetricsCharts({ metrics }) {
  const series = buildSeries(metrics);

  return (
    <section className="glass rounded-2xl p-5">
      <h3 className="font-display text-base font-semibold text-slate-100">Metrics Trends</h3>
      <div className="mt-4 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series}>
            <CartesianGrid stroke="rgba(148,163,184,0.15)" strokeDasharray="4 4" />
            <XAxis dataKey="tick" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "0.8rem",
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="reward" stroke="#29d3a1" dot={false} strokeWidth={2.5} />
            <Line type="monotone" dataKey="accuracy" stroke="#4cc9f0" dot={false} strokeWidth={2.5} />
            <Line type="monotone" dataKey="load" stroke="#ff7f6b" dot={false} strokeWidth={2.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
