import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Landing from "@/pages/Landing";
import Auth from "@/pages/Auth";
import DashboardLayout from "@/pages/dashboard/DashboardLayout";
import Overview from "@/pages/dashboard/Overview";
import Plants from "@/pages/dashboard/Plants";
import Products from "@/pages/dashboard/Products";
import Treatments from "@/pages/dashboard/Treatments";
import Recommendations from "@/pages/dashboard/Recommendations";
import Alerts from "@/pages/dashboard/Alerts";
import Weather from "@/pages/dashboard/Weather";
import Advisor from "@/pages/dashboard/Advisor";
import Fertilization from "@/pages/dashboard/Fertilization";
import Settings from "@/pages/dashboard/Settings";

function Protected({ children }) {
  const { user, checked } = useAuth();
  if (!checked) return <div className="min-h-screen flex items-center justify-center font-mono-tech text-forest-700">Caricamento…</div>;
  if (!user) return <Navigate to="/accedi" replace />;
  return children;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/accedi" element={<Auth />} />
            <Route path="/app" element={<Protected><DashboardLayout /></Protected>}>
              <Route index element={<Overview />} />
              <Route path="piante" element={<Plants />} />
              <Route path="prodotti" element={<Products />} />
              <Route path="trattamenti" element={<Treatments />} />
              <Route path="concimazioni" element={<Fertilization />} />
              <Route path="raccomandazioni" element={<Recommendations />} />
              <Route path="alert" element={<Alerts />} />
              <Route path="meteo" element={<Weather />} />
              <Route path="assistente" element={<Advisor />} />
              <Route path="impostazioni" element={<Settings />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="bottom-right" richColors />
      </AuthProvider>
    </div>
  );
}

export default App;
