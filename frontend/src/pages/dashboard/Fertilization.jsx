import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Leaf, BellRing } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Empty } from "@/components/AgroUI";
import { Modal, ModalHead } from "@/pages/dashboard/Plants";

const TYPES = ["Stallatico", "Letame", "Concime azotato", "Concime potassico", "Concime fosfatico",
  "Concime organico", "Concimazione fogliare", "Cornunghia", "Pollina", "Compost", "Altro"];

const empty = { plant_id: "", ftype: "Stallatico", product_name: "", dose: "", applied_at: "", notes: "", next_reminder_date: "" };

export default function Fertilization() {
  const [items, setItems] = useState([]);
  const [plants, setPlants] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/fertilization").then((r) => setItems(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { ...form, plant_id: form.plant_id || null,
        applied_at: form.applied_at ? new Date(form.applied_at).toISOString() : null,
        next_reminder_date: form.next_reminder_date ? new Date(form.next_reminder_date).toISOString() : null };
      await api.post("/fertilization", payload);
      toast.success("Concimazione registrata");
      setForm(empty); setOpen(false); load();
    } catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  const del = async (id) => { await api.delete(`/fertilization/${id}`); toast.success("Rimossa"); load(); };

  const now = new Date();
  const dueSoon = (d) => d && new Date(d) <= new Date(now.getTime() + 7 * 864e5);

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Nutrizione</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Concimazioni</h1>
          <p className="text-forest-700/70 mt-2">Registra concimazioni (stallatico, letame, azotato…) e imposta promemoria. Il motore ti avvisa quando è il momento.</p>
        </div>
        <button data-testid="add-fert-btn" onClick={() => setOpen(true)} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform">
          <Plus className="w-4 h-4" /> Registra concimazione
        </button>
      </div>

      {items.length === 0 ? (
        <div className="mt-10"><Empty icon={Leaf} text="Nessuna concimazione registrata. Aggiungi la prima e imposta un promemoria (es. stallatico autunnale)." /></div>
      ) : (
        <div className="mt-8 space-y-3">
          {items.map((f, i) => (
            <motion.div key={f.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
              data-testid="fert-row" className="rounded-xl border border-forest-900/10 bg-white p-4 flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-leaf/10 flex items-center justify-center shrink-0"><Leaf className="w-5 h-5 text-leaf" /></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-display font-bold text-forest-900">{f.ftype}</span>
                  {f.product_name && <span className="text-sm text-forest-700/60">· {f.product_name}</span>}
                  <span className="text-xs text-forest-700/50">— {f.plant_name}</span>
                </div>
                <div className="text-xs font-mono-tech text-forest-700/50 mt-0.5">
                  Applicato: {new Date(f.applied_at).toLocaleDateString("it-IT")}{f.dose ? ` · ${f.dose}` : ""}
                </div>
                {f.next_reminder_date && (
                  <div className={`mt-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${dueSoon(f.next_reminder_date) ? "bg-citrus/15 text-citrus" : "bg-secondary text-forest-700/70"}`}>
                    <BellRing className="w-3 h-3" /> Promemoria: {new Date(f.next_reminder_date).toLocaleDateString("it-IT")}
                  </div>
                )}
              </div>
              <button data-testid="delete-fert" onClick={() => del(f.id)} className="text-forest-700/30 hover:text-destructive transition-colors"><Trash2 className="w-4 h-4" /></button>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {open && (
          <Modal onClose={() => setOpen(false)}>
            <form onSubmit={save} data-testid="fert-form">
              <ModalHead title="Registra concimazione" onClose={() => setOpen(false)} />
              <div className="space-y-3">
                <select data-testid="fert-type" value={form.ftype} onChange={set("ftype")} className="inp bg-white">
                  {TYPES.map((t) => <option key={t}>{t}</option>)}
                </select>
                <select data-testid="fert-plant" value={form.plant_id} onChange={set("plant_id")} className="inp bg-white">
                  <option value="">Tutto il frutteto</option>
                  {plants.map((p) => <option key={p.id} value={p.id}>{p.emoji} {p.name}</option>)}
                </select>
                <div className="grid grid-cols-2 gap-3">
                  <input placeholder="Prodotto (opzionale)" value={form.product_name} onChange={set("product_name")} className="inp" />
                  <input placeholder="Dose (es. 3 kg/pianta)" value={form.dose} onChange={set("dose")} className="inp" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-xs text-forest-700/60">Data applicazione<input data-testid="fert-date" type="date" value={form.applied_at} onChange={set("applied_at")} className="inp mt-1" /></label>
                  <label className="text-xs text-forest-700/60">Promemoria prossima<input data-testid="fert-reminder" type="date" value={form.next_reminder_date} onChange={set("next_reminder_date")} className="inp mt-1" /></label>
                </div>
                <textarea placeholder="Note" value={form.notes} onChange={set("notes")} className="inp" rows={2} />
              </div>
              <button data-testid="save-fert" disabled={saving} className="mt-5 w-full rounded-full bg-citrus text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
                {saving ? "Salvataggio…" : "Salva"}
              </button>
            </form>
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}
