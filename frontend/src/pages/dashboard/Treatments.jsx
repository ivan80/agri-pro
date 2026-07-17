import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Syringe } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Empty } from "@/components/AgroUI";
import { Modal, ModalHead } from "@/pages/dashboard/Plants";

const STATUS = { valid: ["Valido", "#16a34a"], leached: ["Dilavato", "#0288D1"],
  expired: ["Scaduto", "#dc2626"], superseded: ["Sostituito", "#8A9A8E"] };

export function TreatmentForm({ plants, products, initial, onSaved, onClose, submitLabel = "Registra" }) {
  const [form, setForm] = useState({ plant_id: initial?.plant_id || "", product_id: initial?.product_id || "",
    dose_used: "", dose_unit: "g", notes: "", applied_at: "" });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { ...form, dose_used: form.dose_used ? Number(form.dose_used) : null,
        applied_at: form.applied_at ? new Date(form.applied_at).toISOString() : null };
      await onSaved(payload);
      onClose();
    } catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  return (
    <form onSubmit={save} data-testid="treatment-form">
      <ModalHead title="Registra trattamento" onClose={onClose} />
      <div className="space-y-3">
        <select data-testid="tr-plant" required value={form.plant_id} onChange={set("plant_id")} className="inp bg-white" disabled={!!initial?.plant_id}>
          <option value="">Seleziona pianta</option>
          {plants.map((p) => <option key={p.id} value={p.id}>{p.emoji} {p.name}</option>)}
        </select>
        <select data-testid="tr-product" required value={form.product_id} onChange={set("product_id")} className="inp bg-white" disabled={!!initial?.product_id}>
          <option value="">Seleziona prodotto</option>
          {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.category})</option>)}
        </select>
        <div className="grid grid-cols-2 gap-3">
          <input type="number" placeholder="Dose usata" value={form.dose_used} onChange={set("dose_used")} className="inp" />
          <input type="date" value={form.applied_at} onChange={set("applied_at")} className="inp" />
        </div>
        <textarea placeholder="Note" value={form.notes} onChange={set("notes")} className="inp" rows={2} />
      </div>
      <button data-testid="save-treatment" disabled={saving} className="mt-5 w-full rounded-full bg-citrus text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
        {saving ? "Salvataggio…" : submitLabel}
      </button>
    </form>
  );
}

export default function Treatments() {
  const [treatments, setTreatments] = useState([]);
  const [plants, setPlants] = useState([]);
  const [products, setProducts] = useState([]);
  const [open, setOpen] = useState(false);

  const load = () => api.get("/treatments").then((r) => setTreatments(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
    api.get("/products").then((r) => setProducts(r.data)).catch(() => {});
  }, []);

  const create = async (payload) => {
    await api.post("/treatments", payload);
    toast.success("Trattamento registrato");
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Quaderno di campagna</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Trattamenti</h1>
        </div>
        <button data-testid="add-treatment-btn" onClick={() => setOpen(true)} disabled={!plants.length || !products.length}
          className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-50">
          <Plus className="w-4 h-4" /> Registra
        </button>
      </div>

      {(!plants.length || !products.length) && (
        <p className="mt-4 text-sm text-citrus">Aggiungi almeno una pianta e un prodotto per registrare i trattamenti.</p>
      )}

      {treatments.length === 0 ? (
        <div className="mt-10"><Empty icon={Syringe} text="Nessun trattamento registrato." /></div>
      ) : (
        <div className="mt-8 rounded-xl border border-forest-900/10 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[#F9F9F6] text-forest-700/60 text-xs uppercase tracking-wider">
              <tr>
                <th className="text-left px-4 py-3">Data</th><th className="text-left px-4 py-3">Pianta</th>
                <th className="text-left px-4 py-3">Prodotto</th><th className="text-left px-4 py-3">Scade</th>
                <th className="text-left px-4 py-3">Stato</th>
              </tr>
            </thead>
            <tbody>
              {treatments.map((t) => {
                const [sl, sc] = STATUS[t.status] || STATUS.valid;
                return (
                  <tr key={t.id} data-testid="treatment-row" className="border-t border-forest-900/5">
                    <td className="px-4 py-3 font-mono-tech text-xs">{new Date(t.applied_at).toLocaleDateString("it-IT")}</td>
                    <td className="px-4 py-3 text-forest-900">{t.plant_name}</td>
                    <td className="px-4 py-3">{t.product_name}</td>
                    <td className="px-4 py-3 font-mono-tech text-xs text-forest-700/60">{t.expires_at ? new Date(t.expires_at).toLocaleDateString("it-IT") : "—"}</td>
                    <td className="px-4 py-3"><span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white" style={{ background: sc }}>{sl}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <AnimatePresence>
        {open && (
          <Modal onClose={() => setOpen(false)}>
            <TreatmentForm plants={plants} products={products} onSaved={create} onClose={() => setOpen(false)} />
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}
