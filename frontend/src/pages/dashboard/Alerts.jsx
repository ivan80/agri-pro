import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, CheckCheck, AlertTriangle, Info, AlertOctagon } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Empty } from "@/components/AgroUI";

const SEV = {
  critical: { color: "#dc2626", icon: AlertOctagon, label: "Critico" },
  warning: { color: "#F57C00", icon: AlertTriangle, label: "Attenzione" },
  info: { color: "#0288D1", icon: Info, label: "Info" },
};

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const load = () => api.get("/alerts").then((r) => setAlerts(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const ack = async (id) => { await api.post(`/alerts/${id}/ack`); load(); };
  const ackAll = async () => { await api.post("/alerts/ack-all"); toast.success("Tutti gli alert letti"); load(); };

  const unread = alerts.filter((a) => !a.acknowledged);

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Notifiche</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Alert</h1>
        </div>
        {unread.length > 0 && (
          <button data-testid="ack-all-btn" onClick={ackAll} className="rounded-full border border-forest-900/15 px-4 py-2 text-sm font-semibold flex items-center gap-2 hover:border-leaf transition-colors">
            <CheckCheck className="w-4 h-4" /> Segna tutti come letti
          </button>
        )}
      </div>

      {alerts.length === 0 ? (
        <div className="mt-10"><Empty icon={Bell} text="Nessun alert. Il motore genera avvisi per dilavamento, scadenza copertura, rischio fungino critico e blocco pioggia." /></div>
      ) : (
        <div className="mt-8 space-y-3">
          {alerts.map((a) => {
            const s = SEV[a.severity] || SEV.info;
            return (
              <motion.div key={a.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
                data-testid="alert-row" className={`rounded-xl border p-4 flex items-start gap-3 ${a.acknowledged ? "border-forest-900/10 bg-white opacity-60" : "border-forest-900/10 bg-white"}`}>
                <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${s.color}1a` }}>
                  <s.icon className="w-4 h-4" style={{ color: s.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase" style={{ color: s.color }}>{s.label}</span>
                    <span className="font-mono-tech text-[10px] text-forest-700/40">{new Date(a.created_at).toLocaleString("it-IT")}</span>
                  </div>
                  <p className="text-sm text-forest-900 mt-0.5">{a.message}</p>
                </div>
                {!a.acknowledged && (
                  <button data-testid="ack-btn" onClick={() => ack(a.id)} className="text-forest-700/40 hover:text-leaf transition-colors"><CheckCheck className="w-5 h-5" /></button>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
