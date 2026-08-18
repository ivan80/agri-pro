import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

export default function Calendar() {
  const [groups, setGroups] = useState([]);
  const [group, setGroup] = useState("pomacee");
  const [months, setMonths] = useState([]);
  const now = new Date().getMonth() + 1;

  useEffect(() => { api.get("/calendar/groups").then((r) => setGroups(r.data)).catch(() => {}); }, []);
  useEffect(() => { api.get(`/calendar/${group}`).then((r) => setMonths(r.data)).catch(() => {}); }, [group]);

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Guida annuale</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Calendario Colturale</h1>
      <p className="text-forest-700/70 mt-2">Le operazioni consigliate mese per mese per ogni gruppo di specie.</p>

      <div className="mt-6 flex gap-2 flex-wrap">
        {groups.map((g) => (
          <button key={g.key} data-testid={`cal-group-${g.key}`} onClick={() => setGroup(g.key)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${group === g.key ? "bg-forest-900 text-white" : "border border-forest-900/15 text-forest-700 hover:border-leaf"}`}>
            {g.emoji} {g.label}
          </button>
        ))}
      </div>

      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {months.map((m, i) => (
          <motion.div key={m.month} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
            data-testid="cal-month" className={`rounded-xl border p-5 ${m.month === now ? "border-citrus bg-citrus/5" : "border-forest-900/10 bg-white"}`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display font-bold text-forest-900">{m.name}</h3>
              {m.month === now && <span className="text-[10px] font-bold uppercase text-citrus">Ora</span>}
            </div>
            <ul className="space-y-1.5">
              {m.operations.map((op, j) => (
                <li key={j} className="text-sm text-forest-700/80 flex items-start gap-2">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-leaf shrink-0" /> {op}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
