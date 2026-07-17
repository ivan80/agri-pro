import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Sparkles, Send, Leaf } from "lucide-react";
import { api, formatApiErrorDetail } from "@/lib/api";
import { toast } from "sonner";

const suggestions = [
  "Come e quando poto un melo giovane?",
  "Quanta acqua serve a un pesco in accrescimento?",
  "Come difendo le ciliegie dalla mosca?",
  "Quale concime uso in fioritura?",
];

export default function Advisor() {
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState("");
  const [messages, setMessages] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { api.get("/plants").then((r) => setPlants(r.data)).catch(() => {}); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const ask = async (text) => {
    const question = text || q;
    if (!question.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setQ(""); setLoading(true);
    try {
      const { data } = await api.post("/ai/advisor", { question, plant_id: plantId || null });
      setMessages((m) => [...m, { role: "ai", text: data.answer }]);
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail));
      setMessages((m) => [...m, { role: "ai", text: "Mi dispiace, non riesco a rispondere in questo momento." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Agronomo digitale</p>
      <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Assistente AI</h1>
      <p className="text-forest-700/70 mt-2">Consigli colturali personalizzati per il tuo frutteto misto.</p>

      <select data-testid="advisor-plant-select" value={plantId} onChange={(e) => setPlantId(e.target.value)}
        className="mt-6 rounded-xl border border-forest-900/15 bg-white px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf">
        <option value="">Domanda generale</option>
        {plants.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.species})</option>)}
      </select>

      <div className="mt-6 rounded-2xl border border-forest-900/10 bg-white p-5 min-h-[340px] flex flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto max-h-[46vh]">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <Sparkles className="w-8 h-8 text-citrus mx-auto mb-3" />
              <p className="text-forest-700/60 text-sm mb-5">Fai una domanda o prova un suggerimento</p>
              <div className="flex flex-wrap justify-center gap-2">
                {suggestions.map((s) => (
                  <button key={s} data-testid="advisor-suggestion" onClick={() => ask(s)} className="text-sm rounded-full border border-forest-900/15 px-3 py-1.5 text-forest-800 hover:border-citrus hover:text-citrus transition-colors">{s}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role === "ai" && <div className="w-8 h-8 rounded-full bg-leaf/15 flex items-center justify-center shrink-0"><Leaf className="w-4 h-4 text-leaf" /></div>}
              <div data-testid={`msg-${m.role}`} className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap max-w-[80%] ${m.role === "user" ? "bg-forest-900 text-white" : "bg-secondary text-forest-900"}`}>{m.text}</div>
            </motion.div>
          ))}
          {loading && <div className="flex gap-3"><div className="w-8 h-8 rounded-full bg-leaf/15 flex items-center justify-center"><Leaf className="w-4 h-4 text-leaf animate-pulse" /></div><div className="rounded-2xl px-4 py-3 bg-secondary text-forest-700/60 text-sm">Sto pensando…</div></div>}
          <div ref={endRef} />
        </div>

        <form onSubmit={(e) => { e.preventDefault(); ask(); }} className="mt-4 flex gap-2 border-t border-forest-900/10 pt-4">
          <input data-testid="advisor-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Scrivi la tua domanda…"
            className="flex-1 rounded-full border border-forest-900/15 px-4 py-2.5 outline-none focus:ring-2 focus:ring-leaf" />
          <button data-testid="advisor-send" disabled={loading} className="rounded-full bg-citrus text-white px-5 py-2.5 flex items-center gap-2 font-semibold hover:-translate-y-0.5 transition-transform disabled:opacity-60">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
