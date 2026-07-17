import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star, Check, X as XIcon } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Empty, PriorityChip } from "@/components/AgroUI";
import { Modal } from "@/pages/dashboard/Plants";
import { TreatmentForm } from "@/pages/dashboard/Treatments";

export default function Recommendations() {
  const [recs, setRecs] = useState([]);
  const [plants, setPlants] = useState([]);
  const [products, setProducts] = useState([]);
  const [exec, setExec] = useState(null);

  const load = () => api.get("/recommendations?status=pending").then((r) => setRecs(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
    api.get("/products").then((r) => setProducts(r.data)).catch(() => {});
  }, []);

  const dismiss = async (id) => { await api.post(`/recommendations/${id}/dismiss`); toast.success("Ignorata"); load(); };
  const execute = async (payload) => {
    await api.post(`/recommendations/${exec.id}/execute`, payload);
    toast.success("Eseguita e registrata nel quaderno");
    load();
  };

  const urgent = recs.filter((r) => r.priority === "urgent");
  const normal = recs.filter((r) => r.priority !== "urgent");

  const Card = ({ r }) => (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} data-testid="rec-card"
      className="rounded-xl border border-forest-900/10 bg-white p-4 flex items-start gap-3">
      <span className="text-2xl">{r.plant_emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-display font-bold text-forest-900">{r.plant_name}</span>
          <PriorityChip priority={r.priority} />
          <span className="font-mono-tech text-[10px] text-forest-700/40 uppercase">{r.reason_code}</span>
        </div>
        <p className="text-sm text-forest-700/80 mt-1">{r.reason}</p>
        <div className="mt-3 flex gap-2">
          {r.product_name && (
            <button data-testid="rec-execute" onClick={() => setExec(r)} className="rounded-full bg-forest-900 text-white text-sm font-semibold px-4 py-1.5 flex items-center gap-1.5 hover:-translate-y-0.5 transition-transform">
              <Check className="w-3.5 h-3.5" /> Esegui ({r.product_name})
            </button>
          )}
          <button data-testid="rec-dismiss" onClick={() => dismiss(r.id)} className="rounded-full border border-forest-900/15 text-sm px-4 py-1.5 flex items-center gap-1.5 hover:border-destructive hover:text-destructive transition-colors">
            <XIcon className="w-3.5 h-3.5" /> Ignora
          </button>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Motore agronomico</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Raccomandazioni</h1>
      <p className="text-forest-700/70 mt-2">Generate dal ciclo motore in base a fase fenologica, rischi e meteo. Esegui il ciclo dalla Dashboard.</p>

      {recs.length === 0 ? (
        <div className="mt-10"><Empty icon={Star} text="Nessuna raccomandazione attiva. Esegui il ciclo motore dalla Dashboard dopo aver configurato piante, fasi correnti e prodotti." /></div>
      ) : (
        <div className="mt-8 space-y-6">
          {urgent.length > 0 && (
            <div><h3 className="font-display font-bold text-forest-900 mb-3">🔴 Urgenti ({urgent.length})</h3>
              <div className="space-y-3">{urgent.map((r) => <Card key={r.id} r={r} />)}</div></div>
          )}
          {normal.length > 0 && (
            <div><h3 className="font-display font-bold text-forest-900 mb-3">Attive ({normal.length})</h3>
              <div className="space-y-3">{normal.map((r) => <Card key={r.id} r={r} />)}</div></div>
          )}
        </div>
      )}

      <AnimatePresence>
        {exec && (
          <Modal onClose={() => setExec(null)}>
            <TreatmentForm plants={plants} products={products}
              initial={{ plant_id: exec.plant_id, product_id: exec.product_id }}
              onSaved={execute} onClose={() => setExec(null)} submitLabel="Esegui trattamento" />
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}
