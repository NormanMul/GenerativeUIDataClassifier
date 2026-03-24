import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import DataCatalog from "./pages/DataCatalog";
import DashboardBuilder from "./pages/DashboardBuilder";
import PipelineExplorer from "./pages/PipelineExplorer";
import GovernanceCenter from "./pages/GovernanceCenter";
import ChatInterface from "./pages/ChatInterface";
import RoleSelector from "./components/RoleSelector";

const navItems = [
  { to: "/", label: "Data Catalog", icon: "📂" },
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/pipeline", label: "Pipeline", icon: "🔗" },
  { to: "/governance", label: "Governance", icon: "🛡️" },
  { to: "/chat", label: "Chat", icon: "💬" },
] as const;

export default function App(): React.JSX.Element {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-udc-blue text-white shadow-md">
          <nav className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
            <span className="text-lg font-bold tracking-tight">UDC Portal</span>
            <div className="flex items-center gap-4">
              {navItems.map(({ to, label, icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-1 text-sm transition-colors ${isActive ? "text-white font-semibold underline underline-offset-4" : "text-blue-200 hover:text-white"}`
                  }
                >
                  <span className="text-xs">{icon}</span>
                  {label}
                </NavLink>
              ))}
            </div>
            <div className="ml-auto">
              <RoleSelector />
            </div>
          </nav>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6">
          <Routes>
            <Route path="/" element={<DataCatalog />} />
            <Route path="/dashboard" element={<DashboardBuilder />} />
            <Route path="/pipeline" element={<PipelineExplorer />} />
            <Route path="/governance" element={<GovernanceCenter />} />
            <Route path="/chat" element={<ChatInterface />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
