import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Users } from "lucide-react";
import Sidebar from "../components/Sidebar";
import StatCard from "../components/StatCard";
import LivePatientViewer from "../components/LivePatientViewer";
import QueueList from "../components/QueueList";
import DecisionLogs from "../components/DecisionLogs";
import MetricsCharts from "../components/MetricsCharts";
import { fetchMetrics, fetchState, resetEnv, sendStep } from "../services/api";
import { createSocket } from "../services/socket";

const EMPTY_METRICS = {
  reward: 0,
  accuracy: 0,
  queue_load: 0,
  response_time: 0,
  reward_history: [],
  accuracy_history: [],
  patient_load_history: [],
  response_time_history: [],
};

export default function DashboardPage() {
  const [state, setState] = useState({
    queue: [],
    current_patient: null,
    last_action: null,
    last_reward: null,
    last_decision_trace: [],
    total_steps: 0,
  });
  const [metrics, setMetrics] = useState(EMPTY_METRICS);
  const [running, setRunning] = useState(false);
  const [autoRun, setAutoRun] = useState(false);

  useEffect(() => {
    async function bootstrap() {
      const [stateRes, metricsRes] = await Promise.all([fetchState(), fetchMetrics()]);
      setState(stateRes);
      setMetrics(metricsRes);
    }
    bootstrap();
  }, []);

  useEffect(() => {
    const disconnect = createSocket((payload) => {
      if (payload.state) {
        setState(payload.state);
      }
      if (payload.metrics) {
        setMetrics(payload.metrics);
      }
    });
    return disconnect;
  }, []);

  useEffect(() => {
    if (!autoRun) {
      return undefined;
    }

    const interval = setInterval(async () => {
      await runStep();
    }, 1800);

    return () => clearInterval(interval);
  }, [autoRun]);

  async function runStep() {
    if (running) {
      return;
    }
    setRunning(true);
    try {
      const payload = await sendStep();
      setState(payload.state);
      setMetrics(payload.metrics);
    } finally {
      setRunning(false);
    }
  }

  async function handleReset() {
    setAutoRun(false);
    const res = await resetEnv();
    setState((prev) => ({ ...prev, ...res, last_decision_trace: [] }));
    const refreshed = await fetchMetrics();
    setMetrics(refreshed);
  }

  const statCards = useMemo(
    () => [
      {
        title: "Avg Reward",
        value: metrics.reward.toFixed(3),
        subtitle: "Policy effectiveness",
        accent: "text-glow",
        icon: CheckCircle2,
      },
      {
        title: "Accuracy",
        value: `${(metrics.accuracy * 100).toFixed(1)}%`,
        subtitle: "Triage + routing precision",
        accent: "text-sky",
        icon: AlertTriangle,
      },
      {
        title: "Queue Load",
        value: String(metrics.queue_load),
        subtitle: "Patients waiting",
        accent: "text-coral",
        icon: Users,
      },
      {
        title: "Response Time",
        value: `${(metrics.response_time * 1000).toFixed(1)} ms`,
        subtitle: "Per-step inference latency",
        accent: "text-amber",
        icon: Clock3,
      },
    ],
    [metrics]
  );

  return (
    <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 gap-6 p-5 lg:grid-cols-[280px_1fr]">
      <Sidebar
        running={running}
        onRunStep={runStep}
        onReset={handleReset}
        autoRun={autoRun}
        onToggleAuto={() => setAutoRun((v) => !v)}
      />

      <main className="space-y-6">
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <StatCard key={card.title} {...card} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
          <LivePatientViewer patient={state.current_patient} />
          <QueueList queue={state.queue} />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <DecisionLogs logs={state.last_decision_trace || []} />
          <MetricsCharts metrics={metrics} />
        </section>
      </main>
    </div>
  );
}
