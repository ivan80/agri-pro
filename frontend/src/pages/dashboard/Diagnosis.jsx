import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Camera, Upload, Sparkles, Stethoscope, Leaf } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Empty } from "@/components/AgroUI";

function resizeToBase64(file, max = 1024) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let { width, height } = img;
        if (width > max || height > max) {
          const r = Math.min(max / width, max / height);
          width = Math.round(width * r); height = Math.round(height * r);
        }
        const c = document.createElement("canvas");
        c.width = width; c.height = height;
        c.getContext("2d").drawImage(img, 0, 0, width, height);
        resolve(c.toDataURL("image/jpeg", 0.85));
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function Diagnosis() {
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState("");
  const [preview, setPreview] = useState(null);
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const fileRef = useRef(null);

  const load = () => api.get("/diagnosis").then((r) => setHistory(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/plants").then((r) => setPlants(r.data)).catch(() => {});
  }, []);

  const pick = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const b64 = await resizeToBase64(f);
      setPreview(b64); setResult(null);
    } catch { toast.error("Impossibile leggere l'immagine"); }
  };

  const analyze = async () => {
    if (!preview) { toast.error("Carica prima una foto"); return; }
    setLoading(true);
    try {
      const { data } = await api.post("/diagnosis", { image_base64: preview, plant_id: plantId || null, notes });
      setResult(data.diagnosis); load();
    } catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail)); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Difesa</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Diagnosi Foto AI</h1>
      <p className="text-forest-700/70 mt-2 max-w-2xl">Scatta o carica una foto di foglia, frutto o rametto: l'AI identifica la malattia/parassita e consiglia il trattamento (con dosi per litro).</p>

      <div className="mt-8 grid lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <select data-testid="diag-plant" value={plantId} onChange={(e) => setPlantId(e.target.value)} className="inp bg-white mb-3">
            <option value="">Diagnosi generale</option>
            {plants.map((p) => <option key={p.id} value={p.id}>{p.emoji} {p.name}</option>)}
          </select>

          <input ref={fileRef} data-testid="diag-file" type="file" accept="image/*" capture="environment" onChange={pick} className="hidden" />
          <button data-testid="diag-upload-btn" onClick={() => fileRef.current?.click()}
            className="w-full rounded-xl border-2 border-dashed border-forest-900/20 p-8 flex flex-col items-center gap-2 hover:border-citrus transition-colors">
            {preview ? (
              <img src={preview} alt="anteprima" className="max-h-56 rounded-lg object-contain" />
            ) : (
              <><Camera className="w-8 h-8 text-leaf" /><span className="text-sm text-forest-700/70">Tocca per scattare o caricare una foto</span></>
            )}
          </button>
          {preview && <button onClick={() => fileRef.current?.click()} className="mt-2 text-sm text-citrus font-semibold flex items-center gap-1"><Upload className="w-3.5 h-3.5" /> Cambia foto</button>}

          <textarea data-testid="diag-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Note (es. macchie sulle foglie da 3 giorni)…" className="inp mt-3" rows={2} />
          <button data-testid="diag-analyze-btn" onClick={analyze} disabled={loading || !preview}
            className="mt-3 w-full rounded-full bg-citrus text-white font-semibold py-3 flex items-center justify-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
            <Sparkles className="w-4 h-4" /> {loading ? "Analisi in corso…" : "Diagnostica con AI"}
          </button>
        </div>

        <div className="rounded-xl border border-forest-900/10 bg-white p-6">
          <h3 className="font-display font-bold text-forest-900 mb-3 flex items-center gap-2"><Stethoscope className="w-5 h-5 text-sky" /> Referto</h3>
          {result ? (
            <div data-testid="diag-result" className="text-sm text-forest-900 whitespace-pre-wrap leading-relaxed">{result}</div>
          ) : (
            <p className="text-forest-700/50 text-sm">Il referto AI comparirà qui dopo l'analisi.</p>
          )}
        </div>
      </div>

      {history.length > 0 && (
        <div className="mt-8">
          <h3 className="font-display font-bold text-forest-900 mb-3">Storico diagnosi</h3>
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} data-testid="diag-history-row" className="rounded-xl border border-forest-900/10 bg-white p-4">
                <div className="flex items-center gap-2 text-xs text-forest-700/50 mb-1">
                  <Leaf className="w-3.5 h-3.5 text-leaf" /> {h.plant_name || "Generale"} · {new Date(h.created_at).toLocaleString("it-IT")}
                </div>
                <div className="text-sm text-forest-900 whitespace-pre-wrap line-clamp-4">{h.diagnosis}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
