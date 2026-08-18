import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ClipboardList, Droplets, AlertTriangle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Empty } from "@/components/AgroUI";

const CAT_COLORS = { rame: "#b45309", fungicida: "#0288D1", zolfo: "#eab308", insetticida: "#F57C00",
  acaricida: "#9333ea", corroborante: "#4CAF50" };

export default function Workplan() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); api.get("/workplan").then((r) => setPlan(r.data)).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Operatività</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Piano di Lavoro</h1>
          <p className="text-forest-700/70 mt-2">Le raccomandazioni attive raggruppate in interventi, con litri di acqua e quantità di prodotto per la vasca.</p>
        </div>
        <button data-testid="workplan-refresh" onClick={load} className="rounded-full border border-forest-900/15 p-3 hover:border-citrus transition-colors"><RefreshCw className={`w-4 h-4 text-forest-800 ${loading ? "animate-spin" : ""}`} /></button>
      </div>

      {plan?.warnings?.length > 0 && (
        <div className="mt-6 space-y-2">
          {plan.warnings.map((w, i) => (
            <div key={i} data-testid="workplan-warning" className="rounded-xl border border-citrus/30 bg-citrus/10 p-3 flex items-center gap-2 text-sm text-forest-900">
              <AlertTriangle className="w-4 h-4 text-citrus shrink-0" /> {w}
            </div>
          ))}
        </div>
      )}

      {!plan?.items?.length ? (
        <div className="mt-10"><Empty icon={ClipboardList} text="Nessun intervento pianificato. Esegui il ciclo motore e assicurati di avere prodotti in magazzino: gli interventi consigliati appariranno qui." /></div>
      ) : (
        <>
          <p className="mt-6 text-sm text-forest-700/60">Base di calcolo: <span className="font-mono-tech text-forest-900">{plan.liters_per_plant} L/pianta</span> · {plan.total_interventi} interventi</p>
          <div className="mt-4 grid md:grid-cols-2 gap-4">
            {plan.items.map((it, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                data-testid="workplan-item" className="rounded-xl border border-forest-900/10 bg-white p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-display font-bold text-forest-900">{it.product}</div>
                  <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white" style={{ background: CAT_COLORS[it.category] || "#666" }}>{it.category}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center mb-3">
                  <div className="rounded-lg bg-[#F9F9F6] p-2"><div className="font-display font-bold text-forest-900">{it.n_plants}</div><div className="text-[10px] text-forest-700/50">piante</div></div>
                  <div className="rounded-lg bg-[#F9F9F6] p-2"><div className="font-display font-bold text-sky flex items-center justify-center gap-1"><Droplets className="w-3.5 h-3.5" />{it.liters}L</div><div className="text-[10px] text-forest-700/50">acqua</div></div>
                  <div className="rounded-lg bg-[#F9F9F6] p-2"><div className="font-display font-bold text-citrus">{it.product_qty != null ? `${it.product_qty}${it.dose_unit}` : "—"}</div><div className="text-[10px] text-forest-700/50">prodotto</div></div>
                </div>
                <div className="text-xs text-forest-700/60">
                  {it.dose_per_l ? `Dose: ${it.dose_per_l}${it.dose_unit}/L · ` : ""}Piante: {it.plants.join(", ")}
                </div>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
