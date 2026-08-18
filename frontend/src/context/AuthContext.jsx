import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken, loadToken } from "@/lib/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    loadToken();
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(false)).finally(() => setChecked(true));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.token) setToken(data.token);
    setUser(data);
    return data;
  };
  const register = async (name, email, password) => {
    const { data } = await api.post("/auth/register", { name, email, password });
    if (data.token) setToken(data.token);
    setUser(data);
    return data;
  };
  const logout = async () => {
    setToken(null);
    setUser(false);
    try { await api.post("/auth/logout"); } catch (e) { /* ignore */ }
  };

  return (
    <AuthContext.Provider value={{ user, checked, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
