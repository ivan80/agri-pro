import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Leaf, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";

export default function Auth() {
  const { login, register } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.name, form.email, form.password);
      toast.success(mode === "login" ? "Bentornato!" : "Account creato — 14 giorni di prova attivi");
      nav("/app");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Errore");
    } finally {
      setLoading(false);
    }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-[#F9F9F6]">
      <div className="hidden lg:block relative overflow-hidden grain">
        <img src="https://images.unsplash.com/photo-1727120279660-5c28b8461609?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwxfHxmcnVpdCUyMG9yY2hhcmR8ZW58MHx8fHwxNzg0MjcyODUxfDA&ixlib=rb-4.1.0&q=85" alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-forest-900/40" />
        <div className="relative z-10 p-12 h-full flex flex-col justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-black text-white text-lg"><Leaf className="w-5 h-5 text-leaf" /> POMARIO</Link>
          <div>
            <h2 className="font-serif-accent italic text-4xl text-white leading-tight">"Il frutteto ricompensa chi lo osserva ogni giorno."</h2>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-6">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="w-full max-w-md">
          <Link to="/" className="lg:hidden flex items-center gap-2 font-display font-black text-forest-900 mb-8"><Leaf className="w-5 h-5 text-leaf" /> POMARIO</Link>
          <h1 className="font-display font-black tracking-tighter text-4xl text-forest-900">{mode === "login" ? "Accedi" : "Crea il tuo account"}</h1>
          <p className="text-forest-700/70 mt-2">{mode === "login" ? "Bentornato nel tuo frutteto digitale." : "Inizia i 14 giorni di prova gratuita."}</p>

          <form onSubmit={submit} className="mt-8 space-y-4" data-testid="auth-form">
            {mode === "register" && (
              <input data-testid="auth-name" required value={form.name} onChange={set("name")} placeholder="Nome" className="w-full rounded-xl border border-forest-900/15 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-leaf" />
            )}
            <input data-testid="auth-email" type="email" required value={form.email} onChange={set("email")} placeholder="Email" className="w-full rounded-xl border border-forest-900/15 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-leaf" />
            <input data-testid="auth-password" type="password" required value={form.password} onChange={set("password")} placeholder="Password" className="w-full rounded-xl border border-forest-900/15 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-leaf" />
            <button data-testid="auth-submit" disabled={loading} className="w-full rounded-full bg-citrus text-white font-semibold py-3.5 flex items-center justify-center gap-2 hover:-translate-y-0.5 transition-transform disabled:opacity-60">
              {loading ? "Attendi…" : mode === "login" ? "Accedi" : "Crea account"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <p className="mt-6 text-sm text-forest-700/70">
            {mode === "login" ? "Non hai un account? " : "Hai già un account? "}
            <button data-testid="auth-switch" onClick={() => setMode(mode === "login" ? "register" : "login")} className="text-citrus font-semibold hover:underline">
              {mode === "login" ? "Registrati" : "Accedi"}
            </button>
          </p>
          <p className="mt-4 font-mono-tech text-xs text-forest-700/40">Demo admin: admin@frutteto.it / Frutteto2026!</p>
        </motion.div>
      </div>
    </div>
  );
}
