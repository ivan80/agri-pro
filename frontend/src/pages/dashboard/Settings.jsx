import { useEffect, useState } from "react";
import { Save, Radio, SlidersHorizontal, MapPin, LocateFixed, Send, Zap } from "lucide-react";
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

  const testTelegram = async () => {
    await save(["telegram_chat_id"]);
    try { await api.post("/telegram/test"); toast.success("Messaggio di prova inviato su Telegram!"); }
    catch (e) { toast.error(e.response?.data?.detail || "Invio non riuscito"); }
  };

  const toggleAuto = async () => {
    const next = cfg.auto_cycle_enabled === "true" ? "false" : "true";
    setCfg({ ...cfg, auto_cycle_enabled: next });
    await api.put("/config", { values: { auto_cycle_enabled: next } });
    toast.success(next === "true" ? "Ciclo automatico attivo (ogni ora)" : "Ciclo automatico disattivato");
  };

  const detectLocation = () => {
    if (!navigator.geolocation) { toast.error("Geolocalizzazione non supportata dal browser"); return; }
    toast.info("Rilevamento posizione…");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCfg((c) => ({ ...c, latitude: pos.coords.latitude.toFixed(4), longitude: pos.coords.longitude.toFixed(4) }));
        toast.success("Posizione rilevata: salva per confermare");
      },
      () => toast.error("Impossibile rilevare la posizione. Inseriscila manualmente."),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className="max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Sistema</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Impostazioni</h1>

      <div className="mt-8 rounded-xl border border-forest-900/10 bg-white p-6">
        <div className="flex items-center gap-2 mb-1"><MapPin className="w-5 h-5 text-leaf" /><h3 className="font-display font-bold text-forest-900">Posizione del frutteto</h3></div>
        <p className="text-sm text-forest-700/70 mb-4">Se non hai una stazione Ecowitt, il meteo viene scaricato in base alla posizione (via Open-Meteo, senza chiavi).</p>
        <div className="grid grid-cols-2 gap-3">
          <input data-testid="cfg-lat" placeholder="Latitudine" value={cfg.latitude || ""} onChange={set("latitude")} className="inp" />
          <input data-testid="cfg-lon" placeholder="Longitudine" value={cfg.longitude || ""} onChange={set("longitude")} className="inp" />
        </div>
        <input data-testid="cfg-locname" placeholder="Località (es. Ponzano Veneto)" value={cfg.location_name || ""} onChange={set("location_name")} className="inp mt-3" />
        <div className="mt-4 flex gap-2 flex-wrap">
          <button data-testid="detect-location" type="button" onClick={detectLocation} className="rounded-full border border-forest-900/15 px-4 py-2.5 text-sm font-semibold flex items-center gap-2 hover:border-leaf transition-colors">
            <LocateFixed className="w-4 h-4" /> Usa la mia posizione
          </button>
          <button data-testid="save-location" onClick={() => save(["latitude", "longitude", "location_name"])} disabled={saving}
            className="rounded-full bg-leaf text-white font-semibold px-5 py-2.5 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
            <Save className="w-4 h-4" /> Salva posizione
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-forest-900/10 bg-white p-6">
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
        <div className="flex items-center gap-2 mb-1"><Send className="w-5 h-5 text-sky" /><h3 className="font-display font-bold text-forest-900">Notifiche Telegram</h3></div>
        <p className="text-sm text-forest-700/70 mb-4">Ricevi su Telegram avvisi, raccomandazioni e promemoria del tuo frutteto.</p>
        <div className="rounded-xl bg-sky/5 border border-sky/20 p-4 mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-sky mb-2">Come collegarti — 3 passi</div>
          <ol className="text-sm text-forest-800 space-y-1.5 list-decimal list-inside">
            <li>Apri Telegram e avvia il <b>bot Pomario</b> premendo <span className="font-mono-tech">/start</span>.</li>
            <li>Scrivi al bot <span className="font-mono-tech">@userinfobot</span>: ti risponderà con la tua <b>Chat ID</b> (un numero, es. 123456789).</li>
            <li>Incolla la Chat ID qui sotto e premi <b>“Salva e invia test”</b>: riceverai un messaggio di conferma.</li>
          </ol>
        </div>
        <input data-testid="cfg-telegram" placeholder="La tua Chat ID (es. 123456789)" value={cfg.telegram_chat_id || ""} onChange={set("telegram_chat_id")} className="inp" />
        <button data-testid="test-telegram" onClick={testTelegram} disabled={saving}
          className="mt-4 rounded-full bg-sky text-white font-semibold px-5 py-2.5 flex items-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
          <Send className="w-4 h-4" /> Salva e invia test
        </button>
      </div>

      <div className="mt-4 rounded-xl border border-forest-900/10 bg-white p-6 flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1"><Zap className="w-5 h-5 text-citrus" /><h3 className="font-display font-bold text-forest-900">Ciclo automatico</h3></div>
          <p className="text-sm text-forest-700/70">Esegue il motore da solo ogni ora (meteo, dilavamento, scadenze, raccomandazioni, promemoria).</p>
        </div>
        <button data-testid="toggle-auto" onClick={toggleAuto}
          className={`shrink-0 w-14 h-8 rounded-full transition-colors relative ${cfg.auto_cycle_enabled === "true" ? "bg-leaf" : "bg-forest-900/15"}`}>
          <span className={`absolute top-1 w-6 h-6 rounded-full bg-white transition-all ${cfg.auto_cycle_enabled === "true" ? "left-7" : "left-1"}`} />
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
