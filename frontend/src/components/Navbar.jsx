import { Bell, Search, Plus, CalendarDays, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";

export default function Navbar({ title, subtitle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const today = new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" });

  return (
    <header className="sticky top-0 z-30 bg-[#F8FAFC]/85 backdrop-blur-xl border-b border-slate-200/60">
      <div className="flex items-center gap-4 px-8 py-4">
        <div className="flex-1 min-w-0">
          <h1 className="font-poppins font-semibold text-2xl text-slate-900 leading-tight" data-testid="page-title">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
        </div>

        <div className="hidden md:flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-4 py-2 w-[320px] shadow-sm">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            data-testid="global-search"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-slate-400"
            placeholder="Search anything..."
          />
          <kbd className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded">⌘K</kbd>
        </div>

        <div className="hidden lg:flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-2 shadow-sm">
          <CalendarDays className="w-4 h-4 text-slate-500" />
          <span className="text-sm text-slate-700 font-medium">{today}</span>
        </div>

        <button
          onClick={() => navigate("/sales/new")}
          data-testid="btn-quick-add"
          className="agri-btn-primary hidden sm:inline-flex"
        >
          <Plus className="w-4 h-4" /> Quick Add
        </button>

        <button className="relative w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition-colors" data-testid="btn-notifications">
          <Bell className="w-4 h-4 text-slate-600" />
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">3</span>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 transition-colors" data-testid="btn-profile">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#15803D] to-[#65A30D] text-white flex items-center justify-center font-poppins font-semibold text-sm">
                {(user?.name || "A").charAt(0).toUpperCase()}
              </div>
              <div className="hidden md:block text-left">
                <div className="text-sm font-semibold text-slate-800 leading-tight">{user?.name || "Admin"}</div>
                <div className="text-[11px] text-slate-500 capitalize">{user?.role || "admin"}</div>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52 rounded-xl">
            <DropdownMenuItem onClick={() => navigate("/settings")} data-testid="menu-settings">Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={async () => { await logout(); navigate("/login"); }} className="text-red-600" data-testid="menu-logout">
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
