import { NavLink, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Package, ShoppingCart, Truck, Users, Building2,
  Layers, BarChart3, Settings, LogOut, Sprout,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";

const items = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", testid: "nav-dashboard", end: true },
  { to: "/products", icon: Package, label: "Products", testid: "nav-products" },
  { to: "/purchase", icon: Truck, label: "Purchase", testid: "nav-purchase" },
  { to: "/sales", icon: ShoppingCart, label: "Sales", testid: "nav-sales" },
  { to: "/customers", icon: Users, label: "Customers", testid: "nav-customers" },
  { to: "/suppliers", icon: Building2, label: "Suppliers", testid: "nav-suppliers" },
  { to: "/batches", icon: Layers, label: "Batch Management", testid: "nav-batches" },
  { to: "/reports", icon: BarChart3, label: "Reports", testid: "nav-reports" },
  { to: "/settings", icon: Settings, label: "Settings", testid: "nav-settings" },
];

export default function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const loc = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <aside className="w-[260px] bg-agri-sidebar text-white h-screen fixed left-0 top-0 flex flex-col z-40" data-testid="sidebar">
      <div className="h-20 flex items-center gap-3 px-6 border-b border-white/10">
        <div className="w-11 h-11 rounded-2xl bg-white flex items-center justify-center shadow-lg">
          <Sprout className="w-6 h-6 text-agri-primary" strokeWidth={2.4} />
        </div>
        <div>
          <div className="font-poppins font-bold text-lg leading-tight">AgriStock</div>
          <div className="text-[11px] text-white/60 tracking-wider uppercase">Inventory ERP</div>
        </div>
      </div>

      <nav className="flex-1 py-4 overflow-y-auto scrollbar-thin">
        {items.map((it) => {
          const Icon = it.icon;
          return (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end}
              data-testid={it.testid}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 mx-3 my-1 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-[#15803D] to-[#65A30D] text-white shadow-lg"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <Icon className="w-[18px] h-[18px]" strokeWidth={2} />
              <span>{it.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-white/10">
        <button
          onClick={handleLogout}
          data-testid="btn-logout"
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white/70 hover:bg-white/10 hover:text-white transition-all"
        >
          <LogOut className="w-[18px] h-[18px]" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
