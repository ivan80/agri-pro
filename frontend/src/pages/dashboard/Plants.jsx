import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Sprout, X } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";

const PHASES = ["riposo", "gemme", "fioritura", "allegagione", "accrescimento", "maturazione"];
const empty = { name: "", species: "Melo", variety: "", planted_year: "", quantity: 1, phase: "riposo", notes: "" };

export default function Plants() {
  const [plants, setPlants] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { ...form, quantity: Number(form.quantity) || 1, planted_year: form.planted_year ? Number(form.planted_year) : null };
      await api.post("/plants", payload);
      toast.success("Pianta aggiunta");
      setForm(empty); setOpen(false); load();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail));
    } finally { setSaving(false); }
  };

  const del = async (id) => {
    await api.delete(`/plants/${id}`);
    toast.success("Pianta rimossa");
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Frutteto</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Le tue piante</h1>
        </div>
        <button data-testid="add-plant-btn" onClick={() => setOpen(true)} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform">
          <Plus className="w-4 h-4" /> Aggiungi pianta
        </button>
      </div>

      {plants.length === 0 ? (
        <div className="mt-12 rounded-2xl border border-dashed border-forest-900/20 p-16 text-center">
          <Sprout className="w-10 h-10 text-leaf mx-auto mb-4" />
          <p className="text-forest-700/70">Nessuna pianta ancora. Aggiungi la prima del tuo frutteto misto.</p>
        </div>
      ) : (
        <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {plants.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              data-testid="plant-card" className="group rounded-xl border border-forest-900/10 bg-white p-5 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-display font-bold text-lg text-forest-900">{p.name}</div>
                  <div className="text-sm text-forest-700/60">{p.species}{p.variety ? ` · ${p.variety}` : ""}</div>
                </div>
                <button data-testid="delete-plant" onClick={() => del(p.id)} className="text-forest-700/30 hover:text-destructive transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
              <div className="mt-4 flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-bold uppercase tracking-wider bg-leaf/15 text-forest-800 rounded-full px-2.5 py-1">{p.phase}</span>
                <span className="text-[10px] font-mono-tech text-forest-700/50">×{p.quantity}</span>
                {p.planted_year && <span className="text-[10px] font-mono-tech text-forest-700/50">dal {p.planted_year}</span>}
              </div>
              {p.notes && <p className="mt-3 text-sm text-forest-700/70">{p.notes}</p>}
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-forest-900/40 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setOpen(false)}>
            <motion.form initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()} onSubmit={save} data-testid="plant-form"
              className="w-full max-w-lg bg-white rounded-2xl p-6 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display font-bold text-xl text-forest-900">Nuova pianta</h2>
                <button type="button" onClick={() => setOpen(false)}><X className="w-5 h-5 text-forest-700" /></button>
              </div>
              <div className="space-y-3">
                <input data-testid="plant-name" required placeholder="Nome (es. Melo del vialetto)" value={form.name} onChange={set("name")} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" />
                <div className="grid grid-cols-2 gap-3">
                  <select data-testid="plant-species" value={form.species} onChange={set("species")} className="rounded-xl border border-forest-900/15 px-4 py-2.5 bg-white outline-none focus:ring-2 focus:ring-leaf">
                    {["Melo", "Pero", "Susino", "Ciliegio", "Albicocco", "Pesco", "Agrume", "Fico", "Kaki", "Altro"].map((s) => <option key={s}>{s}</option>)}
                  </select>
                  <input data-testid="plant-variety" placeholder="Varietà" value={form.variety} onChange={set("variety")} className="rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input data-testid="plant-year" type="number" placeholder="Anno impianto" value={form.planted_year} onChange={set("planted_year")} className="rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" />
                  <input data-testid="plant-qty" type="number" min="1" placeholder="Quantità" value={form.quantity} onChange={set("quantity")} className="rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" />
                </div>
                <select data-testid="plant-phase" value={form.phase} onChange={set("phase")} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 bg-white outline-none focus:ring-2 focus:ring-leaf">
                  {PHASES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
                <textarea data-testid="plant-notes" placeholder="Note (portainnesto, posizione…)" value={form.notes} onChange={set("notes")} className="w-full rounded-xl border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" rows={2} />
              </div>
              <button data-testid="save-plant" disabled={saving} className="mt-5 w-full rounded-full bg-citrus text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
                {saving ? "Salvataggio…" : "Salva pianta"}
              </button>
            </motion.form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
