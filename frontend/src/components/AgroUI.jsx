import { motion } from "framer-motion";

export function RiskBadges({ fungal = 0, insect = 0, acarid = 0, size = "sm" }) {
  const items = [
    { v: fungal, label: "Fungino", color: "#0288D1", short: "F" },
    { v: insect, label: "Insetti", color: "#F57C00", short: "I" },
    { v: acarid, label: "Acari", color: "#9333ea", short: "A" },
  ].filter((i) => i.v > 0);
  if (items.length === 0) return <span className="text-[11px] text-forest-700/40 font-mono-tech">nessun rischio</span>;
  return (
    <div className="flex gap-1.5 flex-wrap">
      {items.map((i) => (
        <span key={i.short} title={`${i.label} ${i.v}/3`}
          className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold text-white"
          style={{ background: i.color, opacity: 0.55 + i.v * 0.15 }}>
          {i.short}{i.v}
        </span>
      ))}
    </div>
  );
}

export function PriorityChip({ priority }) {
  const map = { urgent: ["Urgente", "#dc2626"], normal: ["Normale", "#0288D1"], low: ["Bassa", "#8A9A8E"] };
  const [label, color] = map[priority] || map.normal;
  return <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white" style={{ background: color }}>{label}</span>;
}

export function Empty({ icon: Icon, text }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      className="rounded-2xl border border-dashed border-forest-900/20 p-14 text-center">
      {Icon && <Icon className="w-10 h-10 text-leaf mx-auto mb-4" />}
      <p className="text-forest-700/70">{text}</p>
    </motion.div>
  );
}
