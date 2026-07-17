import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Sprout, Star, ShieldCheck, Bell, Thermometer, Droplets, Wind, Gauge, CloudRain, Play, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PriorityChip } from "@/components/AgroUI";

const kpis = [
  { key: "urgent_recommendations", label: "Raccomandazioni urgenti", icon: Star, color: "#F57C00", to: "/app/raccomandazioni" },
  { key: "pending_recommendations", label: "Raccomandazioni attive", icon: Star, color: "#0288D1", to: "/app/raccomandazioni" },
  { key: "healthy_plants", label: "Piante in salute", icon: ShieldCheck, color: "#4CAF50", to: "/app/piante" },
  { key: "unread_alerts", label: "Alert da leggere", icon: Bell, color: "#eab308", to: "/app/alert" },
];

export default function Overview() {
  const { user } = useAuth();
  const [status, setStatus] = useState({});
  const [irrig, setIrrig] = useState(null);
  const [recs, setRecs] = useState([]);
  const [running, setRunning] = useState(false);

  const load = () => {
    api.get("/status").then((r) => setStatus(r.data)).catch(() => {});
    api.get("/irrigation/status").then((r) => setIrrig(r.data)).catch(() => {});
    api.get("/recommendations?status=pending").then((r) => setRecs(r.data.slice(0, 5))).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const runCycle = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/cycle/run");
      const r = data.result;
      toast.success(`Ciclo eseguito · ${r.new_recommendations} nuove raccomandazioni, rischio fungino ${r.fungal_risk}/3`);
      load();
    } catch (e) { toast.error("Errore durante il ciclo"); }
    finally { setRunning(false); }
  };

  const w = status.weather || {};
  const irrColor = { critical: "#dc2626", low: "#F57C00", ok: "#4CAF50", high: "#0288D1", no_data: "#8A9A8E" }[irrig?.status] || "#8A9A8E";

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Dashboard</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Ciao, {user?.name?.split(" ")[0]} 🌿</h1>
        </div>
        <button data-testid="run-cycle-btn" onClick={runCycle} disabled={running}
          className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Esegui ciclo motore
        </button>
      </div>

      <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((c, i) => (
          <motion.div key={c.key} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Link to={c.to} data-testid={`kpi-${c.key}`} className="block rounded-xl border border-forest-900/10 bg-white p-5 hover:-translate-y-1 hover:shadow-lg transition-[transform,box-shadow]">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: `${c.color}1a` }}>
                <c.icon className="w-5 h-5" style={{ color: c.color }} />
              </div>
              <div className="font-display font-black text-3xl text-forest-900">{status[c.key] ?? 0}</div>
              <div className="text-sm text-forest-700/60 mt-1">{c.label}</div>
            </Link>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 rounded-xl border border-forest-900/10 bg-white p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold text-forest-900">Stazione Ecowitt</h3>
            <span className={`font-mono-tech text-xs ${w.source === "ecowitt" ? "text-leaf" : "text-citrus"}`}>{w.source === "ecowitt" ? "REALE" : w.source ? "DEMO" : "—"}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { icon: Thermometer, l: "Temp", v: w.temp_c != null ? `${w.temp_c}°C` : "—", c: "#F57C00" },
              { icon: Droplets, l: "Umidità", v: w.humidity_pct != null ? `${w.humidity_pct}%` : "—", c: "#0288D1" },
              { icon: Sprout, l: "Suolo", v: w.soil_moisture_pct != null ? `${w.soil_moisture_pct}%` : "—", c: "#4CAF50" },
              { icon: CloudRain, l: "Pioggia", v: w.rainfall_rate_mmh != null ? `${w.rainfall_rate_mmh} mm/h` : "—", c: "#0288D1" },
              { icon: Wind, l: "Vento", v: w.wind_speed_ms != null ? `${w.wind_speed_ms} m/s` : "—", c: "#4FC3F7" },
              { icon: Gauge, l: "Pressione", v: w.pressure_hpa != null ? `${w.pressure_hpa}` : "—", c: "#2F653A" },
            ].map((t) => (
              <div key={t.l} className="rounded-lg bg-[#F9F9F6] p-3">
                <t.icon className="w-4 h-4 mb-1" style={{ color: t.c }} />
                <div className="font-display font-bold text-lg text-forest-900">{t.v}</div>
                <div className="text-[11px] text-forest-700/50">{t.l}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-forest-900/10 bg-white p-6 flex flex-col">
          <h3 className="font-display font-bold text-forest-900 mb-4">Umidità suolo & Irrigazione</h3>
          {irrig ? (
            <div className="flex-1 flex flex-col">
              <div className="font-display font-black text-4xl" style={{ color: irrColor }}>
                {irrig.soil_moisture_pct != null ? `${irrig.soil_moisture_pct}%` : "—"}
              </div>
              <div className="mt-2 h-2 rounded-full bg-secondary overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${irrig.soil_moisture_pct || 0}%`, background: irrColor }} />
              </div>
              <p className="mt-4 text-sm font-semibold text-forest-900">{irrig.message}</p>
              <p className="mt-1 text-sm text-forest-700/70">{irrig.advice}</p>
            </div>
          ) : <p className="text-forest-700/50 text-sm">Caricamento…</p>}
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-forest-900/10 bg-white p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display font-bold text-forest-900">Raccomandazioni urgenti</h3>
          <Link to="/app/raccomandazioni" className="text-sm text-citrus font-semibold hover:underline">Vedi tutte</Link>
        </div>
        {recs.length === 0 ? (
          <p className="text-forest-700/50 text-sm py-6 text-center">Nessuna raccomandazione. Aggiungi piante e prodotti, imposta la fase corrente ed esegui il ciclo motore.</p>
        ) : (
          <div className="space-y-2">
            {recs.map((r) => (
              <div key={r.id} data-testid="overview-rec" className="flex items-center gap-3 rounded-lg border border-forest-900/10 p-3">
                <span className="text-xl">{r.plant_emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-forest-900 text-sm">{r.plant_name}</div>
                  <div className="text-xs text-forest-700/70 truncate">{r.reason}</div>
                </div>
                <PriorityChip priority={r.priority} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
