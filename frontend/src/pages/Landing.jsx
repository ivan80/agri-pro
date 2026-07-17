import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import ReactLenis from "lenis/react";
import { Leaf, Droplets, CloudSun, Wind, Thermometer, Sprout, ArrowRight, Check, Menu, X, Download } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

const IMG = {
  hero: "https://images.unsplash.com/photo-1727120279660-5c28b8461609?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwxfHxmcnVpdCUyMG9yY2hhcmR8ZW58MHx8fHwxNzg0MjcyODUxfDA&ixlib=rb-4.1.0&q=85",
  station: "https://images.unsplash.com/photo-1629204120289-3cb6c195ddde?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzN8MHwxfHNlYXJjaHw0fHx3ZWF0aGVyJTIwc3RhdGlvbnxlbnwwfHx8fDE3ODQyNzI4NTF8MA&ixlib=rb-4.1.0&q=85",
  app: "https://images.unsplash.com/photo-1599591520443-e5045e52d4e6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwyfHxzbWFydCUyMGFncmljdWx0dXJlJTIwdGFibGV0fGVufDB8fHx8MTc4NDI3Mjg1Mnww&ixlib=rb-4.1.0&q=85",
  fruit: "https://images.unsplash.com/photo-1683110752705-f474b57bebc6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHw0fHxmcnVpdCUyMG9yY2hhcmR8ZW58MHx8fHwxNzg0MjcyODUxfDA&ixlib=rb-4.1.0&q=85",
};

const ease = [0.16, 1, 0.3, 1];

const MaskLine = ({ children, delay = 0 }) => (
  <span className="mask-line">
    <motion.span
      className="block"
      initial={{ y: "110%" }}
      animate={{ y: 0 }}
      transition={{ duration: 1, ease, delay }}
    >
      {children}
    </motion.span>
  </span>
);

const Reveal = ({ children, delay = 0, className = "" }) => (
  <motion.div
    className={className}
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-80px" }}
    transition={{ duration: 0.8, ease, delay }}
  >
    {children}
  </motion.div>
);

function Nav() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const links = [["Funzioni", "#funzioni"], ["Fasi", "#fasi"], ["Meteo", "#meteo"], ["Prezzi", "#prezzi"]];
  return (
    <header className="fixed top-0 inset-x-0 z-50 glass border-b border-forest-900/10">
      <nav className="max-w-7xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
        <Link to="/" data-testid="nav-logo" className="flex items-center gap-2 font-display font-black text-lg text-forest-900 tracking-tight">
          <Leaf className="w-5 h-5 text-leaf" /> POMARIO
        </Link>
        <div className="hidden md:flex items-center gap-8">
          {links.map(([l, h]) => (
            <a key={h} href={h} className="text-sm font-medium text-forest-700 hover:text-citrus transition-colors">{l}</a>
          ))}
        </div>
        <div className="hidden md:flex items-center gap-3">
          <Link to={user ? "/app" : "/accedi"} data-testid="nav-cta" className="rounded-full bg-forest-900 text-white text-sm font-semibold px-5 py-2.5 hover:-translate-y-0.5 hover:bg-forest-800 transition-[transform,background-color]">
            {user ? "Apri l'app" : "Inizia la prova"}
          </Link>
        </div>
        <button data-testid="nav-toggle" className="md:hidden text-forest-900" onClick={() => setOpen(!open)}>
          {open ? <X /> : <Menu />}
        </button>
      </nav>
      {open && (
        <div className="md:hidden glass border-t border-forest-900/10 px-6 py-4 flex flex-col gap-4">
          {links.map(([l, h]) => <a key={h} href={h} onClick={() => setOpen(false)} className="text-forest-800 font-medium">{l}</a>)}
          <Link to="/accedi" className="rounded-full bg-forest-900 text-white text-center py-2.5 font-semibold">Inizia la prova</Link>
        </div>
      )}
    </header>
  );
}

function Hero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [0, 180]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.12]);
  return (
    <section ref={ref} className="relative min-h-screen flex flex-col justify-end overflow-hidden grain">
      <motion.div style={{ y, scale }} className="absolute inset-0 z-0">
        <img src={IMG.hero} alt="Frutteto" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#F9F9F6] via-[#F9F9F6]/40 to-transparent" />
      </motion.div>
      <div className="relative z-10 max-w-7xl mx-auto w-full px-6 lg:px-10 pb-20 pt-32">
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="text-xs font-bold uppercase tracking-[0.25em] text-citrus mb-6">
          La cura del frutteto, guidata dai dati
        </motion.p>
        <h1 className="font-display font-black tracking-tighter leading-[0.92] text-forest-900 text-[13vw] sm:text-7xl lg:text-8xl">
          <MaskLine delay={0.15}>Il tuo frutteto,</MaskLine>
          <MaskLine delay={0.3}>
            guidato dalla <span className="font-serif-accent italic font-semibold text-citrus">natura</span>
          </MaskLine>
          <MaskLine delay={0.45}>e dai dati.</MaskLine>
        </h1>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8, ease }}
          className="mt-10 flex flex-col sm:flex-row gap-5 sm:items-center max-w-2xl">
          <p className="text-forest-700/90 text-base lg:text-lg leading-relaxed flex-1">
            Prodotti, irrigazione, fasi fenologiche e la tua stazione meteo Ecowitt — tutto in un'unica app pensata per gli appassionati di frutticoltura.
          </p>
          <Link to="/accedi" data-testid="hero-cta" className="shrink-0 group rounded-full bg-citrus text-white font-semibold px-7 py-4 flex items-center gap-2 hover:-translate-y-1 hover:shadow-xl transition-[transform,box-shadow]">
            Prova 14 giorni gratis <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

function Marquee() {
  const words = ["MELE", "PERE", "SUSINE", "CILIEGIE", "ALBICOCCHE", "PESCHE", "AGRUMI", "FICHI", "KAKI"];
  const row = [...words, ...words];
  return (
    <div className="py-8 bg-forest-900 overflow-hidden border-y border-forest-800">
      <div className="flex whitespace-nowrap animate-marquee">
        {row.map((w, i) => (
          <span key={i} className="font-serif-accent italic text-4xl md:text-6xl text-[#F9F9F6] mx-8 flex items-center gap-8">
            {w} <Sprout className="w-6 h-6 text-leaf inline" />
          </span>
        ))}
      </div>
    </div>
  );
}

const chapters = [
  { n: "01", t: "Anagrafica delle piante", d: "Cataloga ogni albero del tuo frutteto misto: specie, varietà, anno d'impianto e note. Un archivio vivo che cresce con te.", i: IMG.app, side: "left" },
  { n: "02", t: "Irrigazione intelligente", d: "Registra volumi, metodi e durate. Il fabbisogno idrico cambia con la fase fenologica: l'app ti aiuta a non sprecare una goccia.", i: IMG.fruit, side: "right" },
  { n: "03", t: "Fasi fenologiche", d: "Dal riposo vegetativo alla maturazione: segui ogni stadio con consigli mirati su potatura, difesa e concimazione.", i: IMG.hero, side: "left" },
];

function Manifesto() {
  return (
    <section id="funzioni" className="max-w-7xl mx-auto px-6 lg:px-10 py-28 lg:py-40">
      <Reveal>
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-citrus mb-4">Tutto ciò che serve</p>
        <h2 className="font-display font-black tracking-tighter text-4xl md:text-6xl text-forest-900 max-w-3xl leading-none">
          Gestisci il frutteto come un vero agronomo.
        </h2>
      </Reveal>
      <div className="mt-24 flex flex-col gap-28">
        {chapters.map((c, idx) => (
          <div key={c.n} className={`grid md:grid-cols-12 gap-10 items-center ${c.side === "right" ? "md:[direction:rtl]" : ""}`}>
            <Reveal className="md:col-span-5 [direction:ltr]" delay={0.05}>
              <div className="relative">
                <span className="font-serif-accent italic text-8xl text-leaf/30 absolute -top-14 -left-2">{c.n}</span>
                <h3 className="font-display font-bold text-3xl md:text-4xl text-forest-900 relative">{c.t}</h3>
                <p className="mt-5 text-forest-700/80 text-lg leading-relaxed">{c.d}</p>
              </div>
            </Reveal>
            <Reveal className="md:col-span-7 [direction:ltr]" delay={0.15}>
              <div className="overflow-hidden rounded-2xl border border-forest-900/10 shadow-[0_20px_60px_rgba(27,59,34,0.12)]">
                <motion.img whileHover={{ scale: 1.04 }} transition={{ duration: 0.6, ease }}
                  src={c.i} alt={c.t} className="w-full h-[300px] md:h-[420px] object-cover" />
              </div>
            </Reveal>
          </div>
        ))}
      </div>
    </section>
  );
}

const phaseList = [
  { l: "Riposo", m: "Dic–Feb", c: "#8A9A8E" },
  { l: "Gemme", m: "Feb–Mar", c: "#F57C00" },
  { l: "Fioritura", m: "Mar–Apr", c: "#4FC3F7" },
  { l: "Allegagione", m: "Apr–Mag", c: "#81C784" },
  { l: "Accrescimento", m: "Mag–Lug", c: "#4CAF50" },
  { l: "Maturazione", m: "Lug–Ott", c: "#F57C00" },
];

function Phases() {
  return (
    <section id="fasi" className="bg-white border-y border-forest-900/10 py-28">
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <Reveal>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-citrus mb-4">Ciclo naturale</p>
          <h2 className="font-display font-black tracking-tighter text-4xl md:text-5xl text-forest-900 max-w-2xl leading-none">Segui ogni fase fenologica.</h2>
        </Reveal>
        <div className="mt-16 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {phaseList.map((p, i) => (
            <Reveal key={p.l} delay={i * 0.06}>
              <div className="group rounded-2xl border border-forest-900/10 p-6 bg-[#F9F9F6] hover:-translate-y-1 hover:shadow-lg transition-[transform,box-shadow] h-full">
                <div className="w-10 h-10 rounded-full mb-6" style={{ background: p.c }} />
                <div className="font-mono-tech text-xs text-forest-700/60">{p.m}</div>
                <div className="font-display font-bold text-lg text-forest-900 mt-1">{p.l}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Ecowitt() {
  const sensors = [
    { icon: Thermometer, l: "Temperatura", v: "Termo-igrometro" },
    { icon: Droplets, l: "Pioggia", v: "Pluviometro" },
    { icon: Wind, l: "Vento", v: "Anemometro" },
    { icon: CloudSun, l: "Solare & UV", v: "Radiazione" },
  ];
  return (
    <section id="meteo" className="max-w-7xl mx-auto px-6 lg:px-10 py-28 lg:py-40">
      <div className="grid lg:grid-cols-2 gap-14 items-center">
        <Reveal>
          <div className="overflow-hidden rounded-3xl border border-forest-900/10 shadow-[0_20px_60px_rgba(2,136,209,0.15)]">
            <img src={IMG.station} alt="Stazione meteo Ecowitt" className="w-full h-[440px] object-cover" />
          </div>
        </Reveal>
        <div>
          <Reveal>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-sky mb-4">Integrazione Ecowitt</p>
            <h2 className="font-display font-black tracking-tighter text-4xl md:text-5xl text-forest-900 leading-none">
              La tua stazione meteo, <span className="font-serif-accent italic text-sky">in diretta</span>.
            </h2>
            <p className="mt-6 text-forest-700/80 text-lg leading-relaxed">
              Collega la tua stazione Ecowitt completa di tutti i sensori. Temperatura, umidità, pioggia, vento, radiazione solare e umidità del suolo, direttamente nella dashboard del frutteto.
            </p>
          </Reveal>
          <div className="mt-10 grid grid-cols-2 gap-4">
            {sensors.map((s, i) => (
              <Reveal key={s.l} delay={i * 0.06}>
                <div className="flex items-center gap-4 rounded-xl border border-forest-900/10 p-4 bg-white hover:border-sky/40 transition-colors">
                  <div className="w-11 h-11 rounded-lg bg-sky/10 flex items-center justify-center"><s.icon className="w-5 h-5 text-sky" /></div>
                  <div>
                    <div className="font-semibold text-forest-900 text-sm">{s.l}</div>
                    <div className="font-mono-tech text-xs text-forest-700/60">{s.v}</div>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const [plans, setPlans] = useState([]);
  useEffect(() => { api.get("/plans").then((r) => setPlans(r.data)).catch(() => {}); }, []);
  return (
    <section id="prezzi" className="bg-forest-900 grain relative py-28 lg:py-36">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 relative z-10">
        <Reveal>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-citrus mb-4">Prezzi trasparenti</p>
          <h2 className="font-display font-black tracking-tighter text-4xl md:text-6xl text-[#F9F9F6] leading-none max-w-2xl">Prova, abbonati o acquistala per sempre.</h2>
        </Reveal>
        <div className="mt-16 grid md:grid-cols-3 gap-6">
          {plans.map((p, i) => (
            <Reveal key={p.id} delay={i * 0.1}>
              <div className={`relative rounded-3xl p-8 h-full flex flex-col ${p.highlight ? "bg-citrus text-white shadow-[0_0_60px_rgba(245,124,0,0.4)] scale-[1.03]" : "bg-[#F9F9F6] text-forest-900"}`}>
                {p.highlight && <span className="absolute top-5 right-5 text-[10px] font-bold uppercase tracking-widest bg-white/25 rounded-full px-3 py-1">Più scelto</span>}
                <div className="font-display font-bold text-xl">{p.name}</div>
                <div className="mt-4 flex items-end gap-1">
                  <span className="font-display font-black text-5xl tracking-tighter">{p.price}</span>
                  <span className={`mb-2 text-sm ${p.highlight ? "text-white/80" : "text-forest-700/60"}`}>{p.period}</span>
                </div>
                <ul className="mt-8 space-y-3 flex-1">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className={`w-4 h-4 mt-0.5 shrink-0 ${p.highlight ? "text-white" : "text-leaf"}`} /> {f}
                    </li>
                  ))}
                </ul>
                <Link to="/accedi" data-testid={`plan-cta-${p.id}`}
                  className={`mt-8 rounded-full text-center font-semibold py-3.5 transition-[transform,background-color] hover:-translate-y-0.5 ${p.highlight ? "bg-forest-900 text-white hover:bg-forest-800" : "bg-forest-900 text-white hover:bg-forest-800"}`}>
                  {p.id === "trial" ? "Inizia gratis" : "Scegli piano"}
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Download_() {
  return (
    <section className="max-w-7xl mx-auto px-6 lg:px-10 py-28 text-center">
      <Reveal>
        <Download className="w-10 h-10 text-leaf mx-auto mb-6" />
        <h2 className="font-display font-black tracking-tighter text-4xl md:text-6xl text-forest-900 leading-none max-w-3xl mx-auto">Scarica Pomario e cura il tuo frutteto oggi.</h2>
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link to="/accedi" data-testid="download-web" className="rounded-full bg-forest-900 text-white font-semibold px-8 py-4 hover:-translate-y-1 transition-transform">Apri la Web App</Link>
          <a href="#prezzi" className="rounded-full border border-forest-900/20 text-forest-900 font-semibold px-8 py-4 hover:border-citrus hover:text-citrus transition-colors">Vedi i prezzi</a>
        </div>
        <p className="mt-6 font-mono-tech text-xs text-forest-700/50">App per iOS, Android e Web · 14 giorni di prova gratuita</p>
      </Reveal>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-forest-900/10 bg-white">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12 flex flex-col md:flex-row justify-between gap-6">
        <div className="flex items-center gap-2 font-display font-black text-forest-900"><Leaf className="w-5 h-5 text-leaf" /> POMARIO</div>
        <p className="font-mono-tech text-xs text-forest-700/50">© 2026 Pomario · Gestione frutteti misti · Made for growers</p>
      </div>
    </footer>
  );
}

export default function Landing() {
  return (
    <ReactLenis root>
      <div className="bg-[#F9F9F6]">
        <Nav />
        <Hero />
        <Marquee />
        <Manifesto />
        <Phases />
        <Ecowitt />
        <Pricing />
        <Download_ />
        <Footer />
      </div>
    </ReactLenis>
  );
}
