import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency, fmtDate } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, Truck, Search, Pencil, Sparkles } from "lucide-react";
import { toast } from "sonner";
import InvoiceScannerModal from "@/components/InvoiceScannerModal";

export default function Purchase() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [showScanner, setShowScanner] = useState(false);
  const navigate = useNavigate();

  const load = () => api.get("/purchases", { params: { q } }).then((r) => setRows(r.data));
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); /* eslint-disable-next-line */ }, [q]);

  const del = async (id) => {
    if (!window.confirm("Delete this purchase?")) return;
    await api.delete(`/purchases/${id}`);
    toast.success("Purchase deleted");
    load();
  };

  return (
    <>
      <Navbar title="Purchase" subtitle="Manage all purchase invoices from suppliers." />
      <div className="p-8 space-y-6">
        <div className="agri-card p-5 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[280px] relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input className="agri-input pl-10" placeholder="Search invoice or supplier..." value={q} onChange={(e) => setQ(e.target.value)} data-testid="purchase-search" />
          </div>
          <button
            type="button"
            className="bg-emerald-700 hover:bg-emerald-800 text-white font-medium text-sm px-4 py-2.5 rounded-xl flex items-center gap-2 shadow-sm transition-colors"
            onClick={() => setShowScanner(true)}
          >
            <Sparkles className="w-4 h-4 text-lime-300" /> 📸 Scan Paper Invoice (AI)
          </button>
          <button className="agri-btn-primary" onClick={() => navigate("/purchase/new")} data-testid="btn-new-purchase"><Plus className="w-4 h-4" /> New Purchase</button>
        </div>

        <div className="agri-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>{["Invoice", "Supplier", "Date", "Items", "Total", "Paid", "Due", "Actions"].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={8} className="p-16">
                  <div className="flex flex-col items-center text-center">
                    <Truck className="w-14 h-14 text-slate-300 mb-3" />
                    <div className="font-poppins font-medium text-slate-800">No purchases yet</div>
                    <div className="text-sm text-slate-500 mt-1 mb-5">Record your first purchase invoice.</div>
                    <button className="agri-btn-primary" onClick={() => navigate("/purchase/new")}><Plus className="w-4 h-4" /> New Purchase</button>
                  </div>
                </td></tr>
              ) : rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="agri-td font-medium text-agri-primary">{r.invoice_number}</td>
                  <td className="agri-td">{r.supplier_name || "-"}</td>
                  <td className="agri-td">{fmtDate(r.invoice_date)}</td>
                  <td className="agri-td">{(r.items || []).length}</td>
                  <td className="agri-td font-semibold">{fmtCurrency(r.total)}</td>
                  <td className="agri-td">{fmtCurrency(r.paid_amount)}</td>
                  <td className="agri-td text-amber-600 font-medium">{fmtCurrency(r.due_amount)}</td>
                  <td className="agri-td">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => navigate(`/purchase/${r.id}/edit`)}
                        className="w-8 h-8 rounded-lg border border-slate-200 hover:border-agri-primary hover:text-agri-primary flex items-center justify-center transition-colors"
                        title="Edit Purchase"
                        data-testid={`btn-edit-purchase-${r.id}`}
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => del(r.id)}
                        className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center transition-colors"
                        title="Delete Purchase"
                        data-testid={`btn-delete-purchase-${r.id}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <InvoiceScannerModal isOpen={showScanner} onClose={() => setShowScanner(false)} onSuccess={load} />
    </>
  );
}
