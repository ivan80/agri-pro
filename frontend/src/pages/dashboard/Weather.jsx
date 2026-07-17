import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Thermometer, Droplets, Wind, Gauge, CloudRain, Sun, Sprout, RefreshCw, Settings, X } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";

export default function Weather() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCfg, setShowCfg] = useState(false);
  const [cfg, setCfg] = useState({ application_key: "", api_key: "", mac: "" });
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.get("/weather").then((r) => setData(r.data)).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const saveCfg = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/weather/settings", cfg);
      toast.success("Stazione Ecowitt collegata");
      setShowCfg(false); load();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail));
    } finally { setSaving(false); }
  };

  const c = data?.current || {};
  const tiles = [
    { icon: Thermometer, l: "Temperatura", v: `${c.temp ?? "–"}°C`, s: `Percepita ${c.feels_like ?? "–"}°`, color: "#F57C00" },
    { icon: Droplets, l: "Umidità", v: `${c.humidity ?? "–"}%`, s: "Aria esterna", color: "#0288D1" },
    { icon: Wind, l: "Vento", v: `${c.wind_speed ?? "–"} km/h`, s: `Direzione ${c.wind_dir ?? "–"}`, color: "#4FC3F7" },
    { icon: Gauge, l: "Pressione", v: `${c.pressure ?? "–"}`, s: "hPa", color: "#2F653A" },
    { icon: CloudRain, l: "Pioggia oggi", v: `${c.rain_day ?? "–"} mm`, s: `Rate ${c.rain_rate ?? "–"} mm/h`, color: "#0288D1" },
    { icon: Sun, l: "Solare / UV", v: `${c.solar ?? "–"} W/m²`, s: `UV ${c.uv ?? "–"}`, color: "#F57C00" },
    { icon: Sprout, l: "Umidità suolo", v: `${c.soil_moisture ?? "–"}%`, s: `Temp ${c.soil_temp ?? "–"}°C`, color: "#4CAF50" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-sky mb-2">Stazione meteo</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Ecowitt in diretta</h1>
          {data && (
            <p className="text-sm text-forest-700/60 mt-2">
              {data.station} · <span className={`font-mono-tech ${data.source === "ecowitt" ? "text-leaf" : "text-citrus"}`}>{data.source === "ecowitt" ? "DATI REALI" : "MODALITÀ DEMO"}</span>
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button data-testid="weather-refresh" onClick={load} className="rounded-full border border-forest-900/15 p-3 hover:border-sky transition-colors"><RefreshCw className={`w-4 h-4 text-forest-800 ${loading ? "animate-spin" : ""}`} /></button>
          <button data-testid="weather-config-btn" onClick={() => setShowCfg(true)} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform"><Settings className="w-4 h-4" /> Collega stazione</button>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {tiles.map((t, i) => (
          <motion.div key={t.l} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
            data-testid={`weather-tile-${i}`} className="rounded-xl border border-forest-900/10 bg-white p-5">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center mb-3" style={{ background: `${t.color}1a` }}>
              <t.icon className="w-4 h-4" style={{ color: t.color }} />
            </div>
            <div className="text-xs text-forest-700/60">{t.l}</div>
            <div className="font-display font-black text-2xl text-forest-900 mt-1">{t.v}</div>
            <div className="font-mono-tech text-[11px] text-forest-700/50 mt-1">{t.s}</div>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 grid lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <h3 className="font-display font-bold text-forest-900 mb-4">Temperatura · 24h</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data?.history || []}>
              <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#F57C00" stopOpacity={0.3} /><stop offset="100%" stopColor="#F57C00" stopOpacity={0} /></linearGradient></defs>
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#8A9A8E" }} interval={3} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9A8E" }} width={28} />
              <Tooltip />
              <Area type="monotone" dataKey="temp" stroke="#F57C00" strokeWidth={2} fill="url(#tg)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <h3 className="font-display font-bold text-forest-900 mb-4">Umidità · 24h</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data?.history || []}>
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#8A9A8E" }} interval={3} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9A8E" }} width={28} />
              <Tooltip />
              <Line type="monotone" dataKey="humidity" stroke="#0288D1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {showCfg && (
        <div className="fixed inset-0 z-50 bg-forest-900/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setShowCfg(false)}>
          <form onClick={(e) => e.stopPropagation()} onSubmit={saveCfg} data-testid="weather-config-form" className="w-full max-w-lg bg-white rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-bold text-xl text-forest-900">Collega stazione Ecowitt</h2>
              <button type="button" onClick={() => setShowCfg(false)}><X className="w-5 h-5" /></button>
            </div>
            <p className="text-sm text-forest-700/70 mb-4">Inserisci le chiavi dal tuo account Ecowitt (Dashboard → API Management) e il MAC del dispositivo.</p>
            <div className="space-y-3">
              <input data-testid="cfg-appkey" required placeholder="Application Key" value={cfg.application_key} onChange={(e) => setCfg({ ...cfg, application_key: e.target.value })} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-sky" />
              <input data-testid="cfg-apikey" required placeholder="API Key" value={cfg.api_key} onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-sky" />
              <input data-testid="cfg-mac" required placeholder="MAC (AA:BB:CC:DD:EE:FF)" value={cfg.mac} onChange={(e) => setCfg({ ...cfg, mac: e.target.value })} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-sky" />
            </div>
            <button data-testid="save-cfg" disabled={saving} className="mt-5 w-full rounded-full bg-sky text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">{saving ? "Connessione…" : "Salva e connetti"}</button>
          </form>
        </div>
      )}
    </div>
  );
}
