import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

export default function PhasesPage() {
  const [phases, setPhases] = useState([]);
  useEffect(() => { api.get("/phases").then((r) => setPhases(r.data)).catch(() => {}); }, []);

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Guida colturale</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Fasi fenologiche</h1>
      <p className="text-forest-700/70 mt-2 max-w-2xl">Il calendario del frutteto misto: riconosci ogni stadio e applica le cure giuste al momento giusto.</p>

      <div className="mt-8 relative border-l-2 border-forest-900/10 ml-3 pl-8 space-y-8">
        {phases.map((p, i) => (
          <motion.div key={p.key} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}
            data-testid={`phase-${p.key}`} className="relative">
            <span className="absolute -left-[42px] top-1 w-5 h-5 rounded-full border-4 border-[#F9F9F6]" style={{ background: p.color }} />
            <div className="rounded-xl border border-forest-900/10 bg-white p-6">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-display font-bold text-xl text-forest-900">{p.label}</h3>
                <span className="font-mono-tech text-xs text-forest-700/60 rounded-full bg-secondary px-3 py-1">{p.month}</span>
              </div>
              <p className="mt-3 text-forest-700/80">{p.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
