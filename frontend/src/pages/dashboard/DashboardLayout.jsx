import { NavLink, Outlet, useNavigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { LayoutDashboard, Sprout, FlaskConical, Syringe, Star, Bell, CloudSun, Sparkles, Settings2, LogOut, Leaf } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

const groups = [
  { title: "Principale", items: [
    { to: "/app", end: true, icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
    { to: "/app/meteo", icon: CloudSun, label: "Meteo & Ecowitt", id: "weather" },
  ]},
  { title: "Agronomia", items: [
    { to: "/app/piante", icon: Sprout, label: "Piante & Fasi", id: "plants" },
    { to: "/app/raccomandazioni", icon: Star, label: "Raccomandazioni", id: "recs", badgeKey: "pending_recommendations" },
    { to: "/app/trattamenti", icon: Syringe, label: "Trattamenti", id: "treatments" },
    { to: "/app/alert", icon: Bell, label: "Alert", id: "alerts", badgeKey: "unread_alerts" },
  ]},
  { title: "Gestione", items: [
    { to: "/app/prodotti", icon: FlaskConical, label: "Prodotti", id: "products" },
    { to: "/app/assistente", icon: Sparkles, label: "Assistente AI", id: "advisor" },
    { to: "/app/impostazioni", icon: Settings2, label: "Impostazioni", id: "settings" },
  ]},
];

const flat = groups.flatMap((g) => g.items);

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState({});

  useEffect(() => {
    const load = () => api.get("/status").then((r) => setStatus(r.data)).catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const doLogout = async () => { navigate("/"); await logout(); toast.success("Disconnesso"); };

  const linkCls = ({ isActive }) => `flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? "bg-forest-900 text-white" : "text-forest-700 hover:bg-secondary"}`;

  return (
    <div className="min-h-screen flex bg-[#F9F9F6]">
      <aside className="hidden md:flex flex-col w-64 border-r border-forest-900/10 bg-white p-4 fixed h-screen overflow-y-auto">
        <Link to="/" className="flex items-center gap-2 font-display font-black text-forest-900 mb-6 px-2"><Leaf className="w-5 h-5 text-leaf" /> POMARIO</Link>
        <nav className="flex flex-col gap-5 flex-1">
          {groups.map((g) => (
            <div key={g.title}>
              <div className="px-3 mb-1 text-[10px] font-bold uppercase tracking-widest text-forest-700/40">{g.title}</div>
              <div className="flex flex-col gap-0.5">
                {g.items.map((n) => (
                  <NavLink key={n.id} to={n.to} end={n.end} data-testid={`nav-${n.id}`} className={linkCls}>
                    <span className="flex items-center gap-3"><n.icon className="w-4 h-4" /> {n.label}</span>
                    {n.badgeKey && status[n.badgeKey] > 0 && (
                      <span className="text-[10px] font-bold rounded-full bg-citrus text-white px-1.5 min-w-[18px] text-center">{status[n.badgeKey]}</span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="border-t border-forest-900/10 pt-4 mt-4">
          <div className="px-2 mb-3">
            <div className="text-sm font-semibold text-forest-900 truncate">{user?.name}</div>
            <div className="font-mono-tech text-xs text-citrus uppercase">{user?.plan || "trial"}</div>
          </div>
          <button data-testid="logout-btn" onClick={doLogout} className="flex items-center gap-2 text-sm text-forest-700 hover:text-destructive px-2 transition-colors">
            <LogOut className="w-4 h-4" /> Esci
          </button>
        </div>
      </aside>

      <div className="md:hidden fixed bottom-0 inset-x-0 z-40 glass border-t border-forest-900/10 flex justify-around py-2 overflow-x-auto">
        {flat.slice(0, 6).map((n) => (
          <NavLink key={n.id} to={n.to} end={n.end} data-testid={`mnav-${n.id}`}
            className={({ isActive }) => `flex flex-col items-center gap-1 px-2 py-1 text-[10px] ${isActive ? "text-citrus" : "text-forest-700"}`}>
            <n.icon className="w-5 h-5" /> {n.label.split(" ")[0]}
          </NavLink>
        ))}
      </div>

      <main className="flex-1 md:ml-64 p-5 lg:p-8 pb-24 md:pb-8">
        <Outlet />
      </main>
    </div>
  );
}
