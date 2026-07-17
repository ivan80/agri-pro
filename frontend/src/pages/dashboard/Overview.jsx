import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sprout, Layers, Droplets, Waves, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const cards = [
  { key: "plants", label: "Piante gestite", icon: Sprout, color: "#4CAF50" },
  { key: "species", label: "Specie diverse", icon: Layers, color: "#0288D1" },
  { key: "irrigation_events", label: "Irrigazioni", icon: Droplets, color: "#4FC3F7" },
  { key: "total_liters", label: "Litri erogati", icon: Waves, color: "#F57C00" },
];

export default function Overview() {
  const { user } = useAuth();
  const [stats, setStats] = useState({});
  useEffect(() => { api.get("/stats").then((r) => setStats(r.data)).catch(() => {}); }, []);

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Panoramica</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Ciao, {user?.name?.split(" ")[0]} 🌿</h1>
      <p className="text-forest-700/70 mt-2">Ecco lo stato del tuo frutteto oggi.</p>

      <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, i) => (
          <motion.div key={c.key} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            data-testid={`stat-${c.key}`} className="rounded-xl border border-forest-900/10 bg-white p-5">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: `${c.color}1a` }}>
              <c.icon className="w-5 h-5" style={{ color: c.color }} />
            </div>
            <div className="font-display font-black text-3xl text-forest-900">{stats[c.key] ?? 0}</div>
            <div className="text-sm text-forest-700/60 mt-1">{c.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="mt-8 grid md:grid-cols-2 gap-4">
        {[
          { to: "/app/piante", t: "Aggiungi una pianta", d: "Cataloga specie, varietà e anno d'impianto." },
          { to: "/app/meteo", t: "Collega la stazione Ecowitt", d: "Visualizza i dati dei tuoi sensori in diretta." },
          { to: "/app/fasi", t: "Consulta le fasi fenologiche", d: "Consigli per ogni stadio del ciclo." },
          { to: "/app/assistente", t: "Chiedi all'assistente AI", d: "Consigli colturali personalizzati." },
        ].map((a, i) => (
          <motion.div key={a.to} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.06 }}>
            <Link to={a.to} data-testid={`quick-${i}`} className="group flex items-start justify-between rounded-xl border border-forest-900/10 bg-white p-6 hover:-translate-y-1 hover:shadow-lg transition-[transform,box-shadow]">
              <div>
                <div className="font-display font-bold text-lg text-forest-900">{a.t}</div>
                <div className="text-sm text-forest-700/60 mt-1">{a.d}</div>
              </div>
              <ArrowUpRight className="w-5 h-5 text-citrus group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
