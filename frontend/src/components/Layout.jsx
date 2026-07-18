import { Outlet } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import { Toaster } from "sonner";

export default function Layout() {
  return (
    <div className="min-h-screen bg-agri-bg">
      <Sidebar />
      <main className="ml-[260px] min-h-screen">
        <Outlet />
      </main>
      <Toaster position="top-right" richColors closeButton />
    </div>
  );
}
