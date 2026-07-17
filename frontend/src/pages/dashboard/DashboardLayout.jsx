import { NavLink, Outlet, useNavigate, Link } from "react-router-dom";
import { LayoutDashboard, Sprout, CloudSun, GitBranch, Sparkles, LogOut, Leaf } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";

const nav = [
  { to: "/app", end: true, icon: LayoutDashboard, label: "Panoramica", id: "overview" },
  { to: "/app/piante", icon: Sprout, label: "Piante", id: "plants" },
  { to: "/app/meteo", icon: CloudSun, label: "Meteo Ecowitt", id: "weather" },
  { to: "/app/fasi", icon: GitBranch, label: "Fasi Fenologiche", id: "phases" },
  { to: "/app/assistente", icon: Sparkles, label: "Assistente AI", id: "advisor" },
];

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const doLogout = async () => { await logout(); toast.success("Disconnesso"); navigate("/"); };

  return (
    <div className="min-h-screen flex bg-[#F9F9F6]">
      <aside className="hidden md:flex flex-col w-64 border-r border-forest-900/10 bg-white p-5 fixed h-screen">
        <Link to="/" className="flex items-center gap-2 font-display font-black text-forest-900 mb-8 px-2"><Leaf className="w-5 h-5 text-leaf" /> POMARIO</Link>
        <nav className="flex flex-col gap-1 flex-1">
          {nav.map((n) => (
            <NavLink key={n.id} to={n.to} end={n.end} data-testid={`nav-${n.id}`}
              className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? "bg-forest-900 text-white" : "text-forest-700 hover:bg-secondary"}`}>
              <n.icon className="w-4 h-4" /> {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-forest-900/10 pt-4">
          <div className="px-2 mb-3">
            <div className="text-sm font-semibold text-forest-900 truncate">{user?.name}</div>
            <div className="font-mono-tech text-xs text-citrus uppercase">{user?.plan || "trial"}</div>
          </div>
          <button data-testid="logout-btn" onClick={doLogout} className="flex items-center gap-2 text-sm text-forest-700 hover:text-destructive px-2 transition-colors">
            <LogOut className="w-4 h-4" /> Esci
          </button>
        </div>
      </aside>

      <div className="md:hidden fixed bottom-0 inset-x-0 z-40 glass border-t border-forest-900/10 flex justify-around py-2">
        {nav.map((n) => (
          <NavLink key={n.id} to={n.to} end={n.end} data-testid={`mnav-${n.id}`}
            className={({ isActive }) => `flex flex-col items-center gap-1 px-2 py-1 text-[10px] ${isActive ? "text-citrus" : "text-forest-700"}`}>
            <n.icon className="w-5 h-5" /> {n.label.split(" ")[0]}
          </NavLink>
        ))}
      </div>

      <main className="flex-1 md:ml-64 p-6 lg:p-10 pb-24 md:pb-10">
        <Outlet />
      </main>
    </div>
  );
}
