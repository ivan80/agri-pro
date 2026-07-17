import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, X, Sparkles, Check, GitBranch } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { RiskBadges, Empty } from "@/components/AgroUI";

export default function Plants() {
  const [plants, setPlants] = useState([]);
  const [species, setSpecies] = useState([]);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ name: "", species: "Melo", variety: "", notes: "", emoji: "🍎" });
  const [saving, setSaving] = useState(false);
  const [detail, setDetail] = useState(null);

  const load = () => api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/reference/species").then((r) => setSpecies(r.data.species)).catch(() => {});
  }, []);

  const pickSpecies = (name) => {
    const s = species.find((x) => x.name === name);
    setForm({ ...form, species: name, emoji: s?.emoji || "🌳" });
  };

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/plants", form);
      toast.success("Pianta aggiunta con fasi fenologiche generate");
      setForm({ name: "", species: "Melo", variety: "", notes: "", emoji: "🍎" });
      setAddOpen(false); load();
    } catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  const del = async (id) => { await api.delete(`/plants/${id}`); toast.success("Pianta rimossa"); load(); };

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Frutteto</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Piante & Fasi</h1>
        </div>
        <button data-testid="add-plant-btn" onClick={() => setAddOpen(true)} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform">
          <Plus className="w-4 h-4" /> Aggiungi pianta
        </button>
      </div>

      {plants.length === 0 ? (
        <div className="mt-10"><Empty icon={GitBranch} text="Frutteto vuoto. Aggiungi la prima pianta: le fasi fenologiche (scala BBCH) verranno generate in automatico." /></div>
      ) : (
        <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {plants.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              data-testid="plant-card" onClick={() => setDetail(p)}
              className="group cursor-pointer rounded-xl border border-forest-900/10 bg-white p-5 hover:shadow-lg hover:-translate-y-0.5 transition-[transform,box-shadow]">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{p.emoji}</span>
                  <div>
                    <div className="font-display font-bold text-lg text-forest-900">{p.name}</div>
                    <div className="text-sm text-forest-700/60">{p.species}{p.variety ? ` · ${p.variety}` : ""}</div>
                  </div>
                </div>
                <button data-testid="delete-plant" onClick={(e) => { e.stopPropagation(); del(p.id); }} className="text-forest-700/30 hover:text-destructive transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
              <div className="mt-4 rounded-lg bg-[#F9F9F6] p-3">
                <div className="text-[11px] text-forest-700/50 mb-1">Fase attuale</div>
                <div className="font-semibold text-forest-900 text-sm mb-2">{p.current_phase?.phase_name || "—"}</div>
                <RiskBadges fungal={p.current_phase?.risk_fungal} insect={p.current_phase?.risk_insect} acarid={p.current_phase?.risk_acarid} />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {addOpen && (
          <Modal onClose={() => setAddOpen(false)}>
            <form onSubmit={save} data-testid="plant-form">
              <ModalHead title="Nuova pianta" onClose={() => setAddOpen(false)} />
              <div className="space-y-3">
                <input data-testid="plant-name" required placeholder="Nome (es. Melo del vialetto)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="inp" />
                <div className="grid grid-cols-2 gap-3">
                  <select data-testid="plant-species" value={form.species} onChange={(e) => pickSpecies(e.target.value)} className="inp bg-white">
                    {species.map((s) => <option key={s.name} value={s.name}>{s.emoji} {s.name}</option>)}
                  </select>
                  <input data-testid="plant-variety" placeholder="Varietà" value={form.variety} onChange={(e) => setForm({ ...form, variety: e.target.value })} className="inp" />
                </div>
                <textarea data-testid="plant-notes" placeholder="Note (portainnesto, posizione…)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="inp" rows={2} />
                <p className="text-xs text-forest-700/50">Le fasi fenologiche BBCH per «{form.species}» saranno generate automaticamente.</p>
              </div>
              <button data-testid="save-plant" disabled={saving} className="mt-5 w-full rounded-full bg-citrus text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
                {saving ? "Salvataggio…" : "Salva pianta"}
              </button>
            </form>
          </Modal>
        )}
        {detail && <PlantDetail plant={detail} onClose={() => setDetail(null)} onChanged={load} />}
      </AnimatePresence>
    </div>
  );
}

function PlantDetail({ plant, onClose, onChanged }) {
  const [phases, setPhases] = useState([]);
  const [current, setCurrent] = useState(plant.current_phase_id);
  const [aiLoading, setAiLoading] = useState(false);

  const load = () => api.get(`/plants/${plant.id}/phases`).then((r) => setPhases(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const setPhase = async (phaseId) => {
    setCurrent(phaseId);
    await api.post(`/plants/${plant.id}/phase`, { phase_id: phaseId });
    toast.success("Fase corrente aggiornata");
    onChanged();
  };

  const genAI = async () => {
    setAiLoading(true);
    try {
      const { data } = await api.post(`/plants/${plant.id}/generate-phases`);
      toast.success(`${data.count} fasi rigenerate con AI`);
      load(); onChanged();
    } catch (e) { toast.error("Generazione AI non riuscita"); }
    finally { setAiLoading(false); }
  };

  return (
    <Modal onClose={onClose} wide>
      <ModalHead title={`${plant.emoji} ${plant.name}`} onClose={onClose} />
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-forest-700/60">{plant.species}{plant.variety ? ` · ${plant.variety}` : ""} — Fasi fenologiche (BBCH)</p>
        <button data-testid="ai-phases-btn" onClick={genAI} disabled={aiLoading} className="rounded-full border border-forest-900/15 text-sm px-3 py-1.5 flex items-center gap-1.5 hover:border-citrus hover:text-citrus transition-colors disabled:opacity-60">
          <Sparkles className="w-3.5 h-3.5" /> {aiLoading ? "Genero…" : "Rigenera con AI"}
        </button>
      </div>
      <div className="space-y-1.5 max-h-[55vh] overflow-y-auto pr-1">
        {phases.map((ph) => (
          <button key={ph.id} data-testid="phase-row" onClick={() => setPhase(ph.id)}
            className={`w-full text-left rounded-lg border p-3 transition-colors ${current === ph.id ? "border-leaf bg-leaf/5" : "border-forest-900/10 hover:bg-secondary"}`}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono-tech text-xs text-forest-700/40 w-5">{ph.phase_code}</span>
                <span className="font-semibold text-forest-900 text-sm truncate">{ph.phase_name}</span>
                {current === ph.id && <Check className="w-4 h-4 text-leaf shrink-0" />}
              </div>
              <RiskBadges fungal={ph.risk_fungal} insect={ph.risk_insect} acarid={ph.risk_acarid} />
            </div>
            <p className="text-xs text-forest-700/60 mt-1 ml-7">{ph.description}</p>
          </button>
        ))}
      </div>
    </Modal>
  );
}

export function Modal({ children, onClose, wide }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-forest-900/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()} className={`w-full ${wide ? "max-w-2xl" : "max-w-lg"} bg-white rounded-2xl p-6 max-h-[90vh] overflow-y-auto`}>
        {children}
      </motion.div>
    </motion.div>
  );
}

export function ModalHead({ title, onClose }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="font-display font-bold text-xl text-forest-900">{title}</h2>
      <button type="button" onClick={onClose}><X className="w-5 h-5 text-forest-700" /></button>
    </div>
  );
}
