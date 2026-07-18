import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency, fmtDate } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, ShoppingCart, Search, Pencil } from "lucide-react";
import { toast } from "sonner";

export default function Sales() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  const load = () => api.get("/sales", { params: { q } }).then((r) => setRows(r.data));
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); /* eslint-disable-next-line */ }, [q]);

  const del = async (id) => {
    if (!window.confirm("Delete this sale?")) return;
    await api.delete(`/sales/${id}`);
    toast.success("Sale deleted");
    load();
  };

  return (
    <>
      <Navbar title="Sales" subtitle="All sales invoices issued to customers." />
      <div className="p-8 space-y-6">
        <div className="agri-card p-5 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[280px] relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input className="agri-input pl-10" placeholder="Search invoice or customer..." value={q} onChange={(e) => setQ(e.target.value)} data-testid="sales-search" />
          </div>
          <button className="agri-btn-primary" onClick={() => navigate("/sales/new")} data-testid="btn-new-sale"><Plus className="w-4 h-4" /> New Sale</button>
        </div>

        <div className="agri-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100"><tr>{["Invoice", "Customer", "Date", "Items", "Total", "Received", "Balance", "Actions"].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr></thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={8} className="p-16">
                  <div className="flex flex-col items-center text-center">
                    <ShoppingCart className="w-14 h-14 text-slate-300 mb-3" />
                    <div className="font-poppins font-medium text-slate-800">No sales yet</div>
                    <div className="text-sm text-slate-500 mt-1 mb-5">Create your first sales invoice.</div>
                    <button className="agri-btn-primary" onClick={() => navigate("/sales/new")}><Plus className="w-4 h-4" /> New Sale</button>
                  </div>
                </td></tr>
              ) : rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="agri-td font-medium text-agri-primary">{r.invoice_number}</td>
                  <td className="agri-td">{r.customer_name || "Walk-in"}</td>
                  <td className="agri-td">{fmtDate(r.invoice_date)}</td>
                  <td className="agri-td">{(r.items || []).length}</td>
                  <td className="agri-td font-semibold">{fmtCurrency(r.total)}</td>
                  <td className="agri-td">{fmtCurrency(r.received_amount)}</td>
                  <td className="agri-td text-amber-600 font-medium">{fmtCurrency(Math.max(0, r.total - r.received_amount))}</td>
                  <td className="agri-td">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => navigate(`/sales/${r.id}/edit`)}
                        className="w-8 h-8 rounded-lg border border-slate-200 hover:border-agri-primary hover:text-agri-primary flex items-center justify-center transition-colors"
                        title="Edit Sale"
                        data-testid={`btn-edit-sale-${r.id}`}
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => del(r.id)}
                        className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center transition-colors"
                        title="Delete Sale"
                        data-testid={`btn-delete-sale-${r.id}`}
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
    </>
  );
}
