import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Thermometer, Droplets, Wind, Gauge, CloudRain, Sprout, RefreshCw } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import { api } from "@/lib/api";
import { Link } from "react-router-dom";

export default function Weather() {
  const [w, setW] = useState(null);
  const [hist, setHist] = useState([]);
  const [irrig, setIrrig] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.get("/weather/latest").then((r) => setW(r.data)),
      api.get("/weather/history").then((r) => setHist(r.data)),
      api.get("/irrigation/status").then((r) => setIrrig(r.data)),
    ]).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const tiles = w ? [
    { icon: Thermometer, l: "Temperatura", v: `${w.temp_c ?? "–"}°C`, c: "#F57C00" },
    { icon: Droplets, l: "Umidità", v: `${w.humidity_pct ?? "–"}%`, c: "#0288D1" },
    { icon: Sprout, l: "Umidità suolo", v: `${w.soil_moisture_pct ?? "–"}%`, c: "#4CAF50" },
    { icon: CloudRain, l: "Pioggia", v: `${w.rainfall_daily_mm ?? "–"} mm`, c: "#0288D1" },
    { icon: Wind, l: "Vento", v: `${w.wind_speed_ms ?? "–"} m/s`, c: "#4FC3F7" },
    { icon: Gauge, l: "Pressione", v: `${w.pressure_hpa ?? "–"} hPa`, c: "#2F653A" },
  ] : [];

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-sky mb-2">Stazione meteo</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Meteo & Ecowitt</h1>
          {w && <p className="text-sm text-forest-700/60 mt-2">Sorgente: <span className={`font-mono-tech ${w.source === "demo" ? "text-citrus" : "text-leaf"}`}>{w.source === "ecowitt" ? "ECOWITT (REALE)" : w.source === "open-meteo" ? "OPEN-METEO (POSIZIONE)" : "MODALITÀ DEMO"}</span></p>}
        </div>
        <div className="flex gap-2">
          <button data-testid="weather-refresh" onClick={load} className="rounded-full border border-forest-900/15 p-3 hover:border-sky transition-colors"><RefreshCw className={`w-4 h-4 text-forest-800 ${loading ? "animate-spin" : ""}`} /></button>
          <Link to="/app/impostazioni" data-testid="weather-config-link" className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 hover:-translate-y-0.5 transition-transform">Collega stazione</Link>
        </div>
      </div>

      {irrig && (
        <div className="mt-6 rounded-xl border border-forest-900/10 bg-white p-5">
          <div className="flex items-center gap-3">
            <Sprout className="w-5 h-5 text-leaf" />
            <div>
              <div className="font-semibold text-forest-900">{irrig.message}</div>
              <div className="text-sm text-forest-700/70">{irrig.advice}</div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {tiles.map((t, i) => (
          <motion.div key={t.l} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
            data-testid={`weather-tile-${i}`} className="rounded-xl border border-forest-900/10 bg-white p-4">
            <t.icon className="w-4 h-4 mb-2" style={{ color: t.c }} />
            <div className="font-display font-black text-xl text-forest-900">{t.v}</div>
            <div className="text-[11px] text-forest-700/50">{t.l}</div>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 grid lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <h3 className="font-display font-bold text-forest-900 mb-4">Temperatura & Umidità</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={hist}>
              <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#F57C00" stopOpacity={0.3} /><stop offset="100%" stopColor="#F57C00" stopOpacity={0} /></linearGradient></defs>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "#8A9A8E" }} interval="preserveEnd" minTickGap={40} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9A8E" }} width={28} />
              <Tooltip />
              <Area type="monotone" dataKey="temp" name="Temp °C" stroke="#F57C00" strokeWidth={2} fill="url(#tg)" />
              <Line type="monotone" dataKey="humidity" name="Umidità %" stroke="#0288D1" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <h3 className="font-display font-bold text-forest-900 mb-4">Umidità suolo & Pioggia</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={hist}>
              <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4CAF50" stopOpacity={0.3} /><stop offset="100%" stopColor="#4CAF50" stopOpacity={0} /></linearGradient></defs>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "#8A9A8E" }} interval="preserveEnd" minTickGap={40} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9A8E" }} width={28} />
              <Tooltip />
              <Area type="monotone" dataKey="soil" name="Suolo %" stroke="#4CAF50" strokeWidth={2} fill="url(#sg)" />
              <Line type="monotone" dataKey="rain" name="Pioggia mm" stroke="#0288D1" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
