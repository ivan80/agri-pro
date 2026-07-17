import { useEffect, useState } from "react";
import { Save, Radio, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

const THRESHOLDS = [
  { key: "rain_block_mmh", label: "Pioggia blocco trattamenti (mm/h)" },
  { key: "leaching_threshold_mm", label: "Soglia dilavamento (mm)" },
  { key: "leaf_wetness_threshold", label: "Bagnatura fogliare soglia (0-8)" },
  { key: "temp_fungal_min_c", label: "Temp min rischio fungino (°C)" },
  { key: "temp_fungal_max_c", label: "Temp max rischio fungino (°C)" },
  { key: "humidity_fungal_threshold", label: "Umidità soglia fungino (%)" },
  { key: "soil_moisture_low_pct", label: "Umidità suolo bassa (%)" },
  { key: "soil_moisture_critical_pct", label: "Umidità suolo critica (%)" },
  { key: "soil_moisture_stop_pct", label: "Umidità suolo stop irrigazione (%)" },
];

export default function Settings() {
  const [cfg, setCfg] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.get("/config").then((r) => setCfg(r.data)).catch(() => {}); }, []);
  const set = (k) => (e) => setCfg({ ...cfg, [k]: e.target.value });

  const save = async (keys) => {
    setSaving(true);
    try {
      const values = {};
      keys.forEach((k) => (values[k] = String(cfg[k] ?? "")));
      await api.put("/config", { values });
      toast.success("Impostazioni salvate");
    } catch (e) { toast.error("Errore nel salvataggio"); }
    finally { setSaving(false); }
  };

  return (
    <div className="max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Sistema</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Impostazioni</h1>

      <div className="mt-8 rounded-xl border border-forest-900/10 bg-white p-6">
        <div className="flex items-center gap-2 mb-1"><Radio className="w-5 h-5 text-sky" /><h3 className="font-display font-bold text-forest-900">Stazione Ecowitt</h3></div>
        <p className="text-sm text-forest-700/70 mb-4">Chiavi dal tuo account Ecowitt (Dashboard → API Management) e MAC del dispositivo. Senza chiavi il meteo resta in modalità demo.</p>
        <div className="space-y-3">
          <input data-testid="cfg-appkey" placeholder="Application Key" value={cfg.ecowitt_app_key || ""} onChange={set("ecowitt_app_key")} className="inp" />
          <input data-testid="cfg-apikey" placeholder="API Key" value={cfg.ecowitt_api_key || ""} onChange={set("ecowitt_api_key")} className="inp" />
          <input data-testid="cfg-mac" placeholder="MAC (AA:BB:CC:DD:EE:FF)" value={cfg.ecowitt_mac || ""} onChange={set("ecowitt_mac")} className="inp" />
        </div>
        <button data-testid="save-ecowitt" onClick={() => save(["ecowitt_app_key", "ecowitt_api_key", "ecowitt_mac"])} disabled={saving}
          className="mt-4 rounded-full bg-sky text-white font-semibold px-5 py-2.5 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
          <Save className="w-4 h-4" /> Salva e connetti
        </button>
      </div>

      <div className="mt-4 rounded-xl border border-forest-900/10 bg-white p-6">
        <div className="flex items-center gap-2 mb-4"><SlidersHorizontal className="w-5 h-5 text-forest-700" /><h3 className="font-display font-bold text-forest-900">Soglie del motore agronomico</h3></div>
        <div className="grid sm:grid-cols-2 gap-4">
          {THRESHOLDS.map((t) => (
            <label key={t.key} className="text-sm text-forest-700/70">
              {t.label}
              <input data-testid={`cfg-${t.key}`} type="number" value={cfg[t.key] ?? ""} onChange={set(t.key)} className="inp mt-1" />
            </label>
          ))}
        </div>
        <button data-testid="save-thresholds" onClick={() => save(THRESHOLDS.map((t) => t.key))} disabled={saving}
          className="mt-5 rounded-full bg-forest-900 text-white font-semibold px-5 py-2.5 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
          <Save className="w-4 h-4" /> Salva soglie
        </button>
      </div>
    </div>
  );
}
