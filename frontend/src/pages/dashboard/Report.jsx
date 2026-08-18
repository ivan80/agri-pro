import { useEffect, useState } from "react";
import { FileText, Printer, Leaf } from "lucide-react";
import { api } from "@/lib/api";

export default function Report() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/report").then((r) => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <p className="text-forest-700/50">Caricamento…</p>;
  const c = data.counts;

  const Section = ({ title, children }) => (
    <div className="mt-6"><h3 className="font-display font-bold text-forest-900 mb-2">{title}</h3>{children}</div>
  );
  const Table = ({ head, rows }) => (
    <div className="rounded-lg border border-forest-900/10 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-[#F9F9F6] text-forest-700/60 text-xs uppercase"><tr>{head.map((h) => <th key={h} className="text-left px-3 py-2">{h}</th>)}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-4 print:hidden">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-citrus mb-2">Quaderno di campagna</p>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">Report</h1>
        </div>
        <button data-testid="print-report-btn" onClick={() => window.print()} className="rounded-full bg-forest-900 text-white font-semibold px-5 py-3 flex items-center gap-2 hover:-translate-y-0.5 transition-transform">
          <Printer className="w-4 h-4" /> Stampa / Salva PDF
        </button>
      </div>

      <div data-testid="report-content" className="mt-6 bg-white rounded-xl border border-forest-900/10 p-8">
        <div className="flex items-center gap-2 border-b border-forest-900/10 pb-4 mb-4">
          <Leaf className="w-6 h-6 text-leaf" />
          <div>
            <div className="font-display font-black text-xl text-forest-900">Pomario — Quaderno di Campagna</div>
            <div className="text-xs text-forest-700/50">{data.owner} · generato il {new Date(data.generated_at).toLocaleString("it-IT")}</div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3">
          {[["Piante", c.plants], ["Trattamenti", c.treatments], ["Concimazioni", c.fertilizations], ["Diagnosi", c.diagnoses]].map(([l, v]) => (
            <div key={l} className="rounded-lg bg-[#F9F9F6] p-3 text-center">
              <div className="font-display font-black text-2xl text-forest-900">{v}</div>
              <div className="text-[11px] text-forest-700/50">{l}</div>
            </div>
          ))}
        </div>

        <Section title="Piante">
          <Table head={["", "Nome", "Specie", "Fase attuale"]} rows={data.plants.map((p, i) => (
            <tr key={i} className="border-t border-forest-900/5"><td className="px-3 py-2">{p.emoji}</td><td className="px-3 py-2 text-forest-900">{p.name}</td><td className="px-3 py-2">{p.species} {p.variety}</td><td className="px-3 py-2">{p.phase}</td></tr>
          ))} />
        </Section>

        <Section title="Trattamenti recenti">
          {data.treatments.length ? <Table head={["Data", "Pianta", "Prodotto", "Stato"]} rows={data.treatments.map((t, i) => (
            <tr key={i} className="border-t border-forest-900/5"><td className="px-3 py-2 font-mono-tech text-xs">{t.date}</td><td className="px-3 py-2">{t.plant}</td><td className="px-3 py-2">{t.product}</td><td className="px-3 py-2">{t.status}</td></tr>
          ))} /> : <p className="text-sm text-forest-700/50">Nessun trattamento.</p>}
        </Section>

        <Section title="Concimazioni">
          {data.fertilizations.length ? <Table head={["Data", "Tipo", "Prodotto", "Dose"]} rows={data.fertilizations.map((f, i) => (
            <tr key={i} className="border-t border-forest-900/5"><td className="px-3 py-2 font-mono-tech text-xs">{f.date}</td><td className="px-3 py-2">{f.type}</td><td className="px-3 py-2">{f.product}</td><td className="px-3 py-2">{f.dose}</td></tr>
          ))} /> : <p className="text-sm text-forest-700/50">Nessuna concimazione.</p>}
        </Section>

        {data.diagnoses.length > 0 && (
          <Section title="Diagnosi">
            <div className="space-y-2">{data.diagnoses.map((d, i) => (
              <div key={i} className="rounded-lg border border-forest-900/10 p-3 text-sm"><span className="font-mono-tech text-xs text-forest-700/50">{d.date}</span> — {d.summary}</div>
            ))}</div>
          </Section>
        )}
      </div>
    </div>
  );
}
