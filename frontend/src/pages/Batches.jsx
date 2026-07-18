import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtDate } from "@/lib/api";
import { Layers, AlertTriangle } from "lucide-react";

export default function Batches() {
  const [rows, setRows] = useState([]);
  const [tab, setTab] = useState("all");
  const load = async () => {
    const url = tab === "expiring" ? "/batches/expiring" : "/batches";
    const { data } = await api.get(url);
    setRows(data);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [tab]);

  const today = new Date().toISOString().slice(0, 10);

  return (
    <>
      <Navbar title="Batch Management" subtitle="Track product batches with FIFO logic and expiry alerts." />
      <div className="p-8 space-y-6">
        <div className="flex items-center gap-3">
          {[
            { k: "all", label: "All Batches" },
            { k: "expiring", label: "Expiring Soon (90 days)" },
          ].map((t) => (
            <button key={t.k} onClick={() => setTab(t.k)} data-testid={`tab-${t.k}`}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${tab === t.k ? "bg-gradient-to-r from-[#15803D] to-[#65A30D] text-white shadow-button" : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"}`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="agri-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100"><tr>{["Product", "Batch No.", "Mfg Date", "Expiry Date", "Warehouse", "Rack", "Stock", "Status"].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr></thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={8} className="p-16">
                  <div className="flex flex-col items-center text-center">
                    <Layers className="w-14 h-14 text-slate-300 mb-3" />
                    <div className="font-poppins font-medium text-slate-800">No batch data yet</div>
                    <div className="text-sm text-slate-500 mt-1">Add products with batch numbers & expiry dates to see them here.</div>
                  </div>
                </td></tr>
              ) : rows.map((p) => {
                const expired = p.expiry_date && p.expiry_date < today;
                const soon = p.expiry_date && p.expiry_date <= new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10);
                return (
                  <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                    <td className="agri-td font-medium text-slate-800">{p.name}</td>
                    <td className="agri-td font-mono text-xs">{p.batch_number || "-"}</td>
                    <td className="agri-td">{fmtDate(p.manufacture_date)}</td>
                    <td className={`agri-td font-medium ${expired ? "text-red-600" : soon ? "text-amber-600" : "text-slate-700"}`}>{fmtDate(p.expiry_date)}</td>
                    <td className="agri-td">Main</td>
                    <td className="agri-td">{p.rack_number || "-"}</td>
                    <td className="agri-td font-semibold">{p.current_stock} {p.unit}</td>
                    <td className="agri-td">
                      {expired ? <span className="agri-badge bg-red-100 text-red-700 gap-1"><AlertTriangle className="w-3 h-3" />Expired</span>
                        : soon ? <span className="agri-badge bg-amber-100 text-amber-700">Expiring Soon</span>
                          : <span className="agri-badge bg-emerald-100 text-emerald-700">Active</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
