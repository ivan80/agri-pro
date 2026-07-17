import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, FlaskConical, Package, PackageX } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Empty } from "@/components/AgroUI";
import { Modal, ModalHead } from "@/pages/dashboard/Plants";

const CAT_COLORS = { rame: "#b45309", fungicida: "#0288D1", zolfo: "#eab308", insetticida: "#F57C00",
  acaricida: "#9333ea", corroborante: "#4CAF50", correttore: "#0ea5e9", fertilizzante: "#16a34a", ammendante: "#78716c" };

const empty = { name: "", active_ingredient: "", category: "fungicida", persistence_days: 7,
  carenza_days: 0, dose_per_hl: "", dose_unit: "g", leaching_threshold_mm: 15, notes: "", in_stock: true };

export default function Products() {
  const [products, setProducts] = useState([]);
  const [cats, setCats] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/products").then((r) => setProducts(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/reference/categories").then((r) => setCats(r.data.categories)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { ...form, persistence_days: Number(form.persistence_days) || 7,
        carenza_days: Number(form.carenza_days) || 0, leaching_threshold_mm: Number(form.leaching_threshold_mm) || 15,
        dose_per_hl: form.dose_per_hl ? Number(form.dose_per_hl) : null };
      await api.post("/products", payload);
      toast.success("Prodotto aggiunto");
      setForm(empty); setOpen(false); load();
    } catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  const toggleStock = async (p) => {
    await api.put(`/products/${p.id}`, { ...p, in_stock: !p.in_stock });
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Magazzino</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Prodotti fitosanitari</h1>
        </div>
        <button data-testid="add-product-btn" onClick={() => setOpen(true)} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform">
          <Plus className="w-4 h-4" /> Aggiungi prodotto
        </button>
      </div>

      {products.length === 0 ? (
        <div className="mt-10"><Empty icon={FlaskConical} text="Magazzino vuoto. Aggiungi i tuoi prodotti (rame, fungicidi, insetticidi…): il motore li userà per le raccomandazioni." /></div>
      ) : (
        <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              data-testid="product-card" className="rounded-xl border border-forest-900/10 bg-white p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-display font-bold text-forest-900">{p.name}</div>
                  <div className="text-xs text-forest-700/60">{p.active_ingredient || "—"}</div>
                </div>
                <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white" style={{ background: CAT_COLORS[p.category] || "#666" }}>{p.category}</span>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                {[["Persist.", `${p.persistence_days}g`], ["Carenza", `${p.carenza_days}g`], ["Dilav.", `${p.leaching_threshold_mm}mm`]].map(([l, v]) => (
                  <div key={l} className="rounded-lg bg-[#F9F9F6] p-2">
                    <div className="font-display font-bold text-forest-900 text-sm">{v}</div>
                    <div className="text-[10px] text-forest-700/50">{l}</div>
                  </div>
                ))}
              </div>
              <button data-testid="toggle-stock" onClick={() => toggleStock(p)}
                className={`mt-3 w-full rounded-lg py-2 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${p.in_stock ? "bg-leaf/10 text-forest-800" : "bg-secondary text-forest-700/50"}`}>
                {p.in_stock ? <Package className="w-4 h-4" /> : <PackageX className="w-4 h-4" />} {p.in_stock ? "In magazzino" : "Esaurito"}
              </button>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {open && (
          <Modal onClose={() => setOpen(false)}>
            <form onSubmit={save} data-testid="product-form">
              <ModalHead title="Nuovo prodotto" onClose={() => setOpen(false)} />
              <div className="space-y-3">
                <input data-testid="product-name" required placeholder="Nome commerciale" value={form.name} onChange={set("name")} className="inp" />
                <div className="grid grid-cols-2 gap-3">
                  <input placeholder="Principio attivo" value={form.active_ingredient} onChange={set("active_ingredient")} className="inp" />
                  <select data-testid="product-category" value={form.category} onChange={set("category")} className="inp bg-white">
                    {cats.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <label className="text-xs text-forest-700/60">Persistenza (gg)<input type="number" value={form.persistence_days} onChange={set("persistence_days")} className="inp mt-1" /></label>
                  <label className="text-xs text-forest-700/60">Carenza (gg)<input type="number" value={form.carenza_days} onChange={set("carenza_days")} className="inp mt-1" /></label>
                  <label className="text-xs text-forest-700/60">Dilav. (mm)<input type="number" value={form.leaching_threshold_mm} onChange={set("leaching_threshold_mm")} className="inp mt-1" /></label>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input type="number" placeholder="Dose per hl" value={form.dose_per_hl} onChange={set("dose_per_hl")} className="inp" />
                  <select value={form.dose_unit} onChange={set("dose_unit")} className="inp bg-white">
                    {["g", "ml", "kg", "l"].map((u) => <option key={u}>{u}</option>)}
                  </select>
                </div>
                <textarea placeholder="Note (es. MAI con zolfo)" value={form.notes} onChange={set("notes")} className="inp" rows={2} />
              </div>
              <button data-testid="save-product" disabled={saving} className="mt-5 w-full rounded-full bg-citrus text-white font-semibold py-3 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
                {saving ? "Salvataggio…" : "Salva prodotto"}
              </button>
            </form>
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}
