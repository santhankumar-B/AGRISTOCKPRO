import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency, fmtDate } from "@/lib/api";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, RefreshCcw, FileSpreadsheet, Printer, Pencil, Trash2, PackageSearch } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [company, setCompany] = useState("");
  const [stock, setStock] = useState("");
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/products", { params: { q, category, company, stock } });
      setProducts(data);
    } catch {
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [q, category, company, stock]);

  const categories = [...new Set(products.map((p) => p.category).filter(Boolean))];
  const companies = [...new Set(products.map((p) => p.company).filter(Boolean))];

  const exportExcel = () => {
    const rows = [
      ["Barcode", "Name", "Category", "Company", "Batch", "Mfg Date", "Expiry", "Stock", "Unit", "Purchase Price", "Selling Price"],
      ...products.map((p) => [p.barcode, p.name, p.category, p.company, p.batch_number, p.manufacture_date, p.expiry_date, p.current_stock, p.unit, p.purchase_price, p.selling_price]),
    ];
    const csv = rows.map((r) => r.map((v) => `"${(v ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "products.csv"; a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported to CSV");
  };

  const del = async (p) => {
    if (!window.confirm(`Delete "${p.name}"?`)) return;
    await api.delete(`/products/${p.id}`);
    toast.success("Product deleted");
    load();
  };

  const statusBadge = (p) => {
    const today = new Date().toISOString().slice(0, 10);
    if (p.expiry_date && p.expiry_date < today) return { label: "Expired", cls: "bg-red-100 text-red-700" };
    if (p.expiry_date && p.expiry_date <= new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10)) return { label: "Expiring Soon", cls: "bg-amber-100 text-amber-700" };
    if (p.current_stock <= 0) return { label: "Out of Stock", cls: "bg-red-100 text-red-700" };
    if (p.current_stock <= p.minimum_stock) return { label: "Low Stock", cls: "bg-amber-100 text-amber-700" };
    return { label: "In Stock", cls: "bg-emerald-100 text-emerald-700" };
  };

  return (
    <>
      <Navbar title="Products" subtitle="Manage your product catalog, batches and stock levels." />
      <div className="p-8 space-y-6">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="agri-card p-5">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[240px]">
              <label className="agri-label">Search</label>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input data-testid="product-search" className="agri-input pl-10" placeholder="Search product name, barcode, batch..." value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
            </div>
            <div className="min-w-[160px]">
              <label className="agri-label">Category</label>
              <select className="agri-input" value={category} onChange={(e) => setCategory(e.target.value)} data-testid="filter-category">
                <option value="">All Categories</option>
                {categories.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="min-w-[160px]">
              <label className="agri-label">Company</label>
              <select className="agri-input" value={company} onChange={(e) => setCompany(e.target.value)} data-testid="filter-company">
                <option value="">All Companies</option>
                {companies.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="min-w-[140px]">
              <label className="agri-label">Stock</label>
              <select className="agri-input" value={stock} onChange={(e) => setStock(e.target.value)} data-testid="filter-stock">
                <option value="">All Status</option>
                <option value="in">In Stock</option>
                <option value="low">Low Stock</option>
                <option value="out">Out of Stock</option>
              </select>
            </div>
            <button className="agri-btn-secondary" onClick={load} data-testid="btn-refresh"><RefreshCcw className="w-4 h-4" /> Refresh</button>
            <button className="agri-btn-secondary" onClick={exportExcel} data-testid="btn-export"><FileSpreadsheet className="w-4 h-4" /> Export</button>
            <button className="agri-btn-secondary" onClick={() => window.print()} data-testid="btn-print"><Printer className="w-4 h-4" /> Print</button>
            <button className="agri-btn-primary" onClick={() => navigate("/products/new")} data-testid="btn-add-product"><Plus className="w-4 h-4" /> Add Product</button>
          </div>
        </motion.div>

        <div className="agri-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  {["Image", "Barcode", "Product", "Category", "Company", "Batch", "Mfg", "Expiry", "Stock", "Unit", "Status", "Actions"].map((h) => (
                    <th key={h} className="agri-th">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  [...Array(6)].map((_, i) => (
                    <tr key={i} className="border-b border-slate-100"><td colSpan={12}><div className="h-14 animate-pulse bg-slate-50 m-2 rounded" /></td></tr>
                  ))
                ) : products.length === 0 ? (
                  <tr><td colSpan={12}>
                    <div className="flex flex-col items-center justify-center p-16 text-center">
                      <PackageSearch className="w-14 h-14 text-slate-300 mb-3" />
                      <div className="font-poppins font-medium text-slate-800">No products yet</div>
                      <div className="text-sm text-slate-500 mt-1 mb-5">Add your first product to start managing inventory.</div>
                      <button className="agri-btn-primary" onClick={() => navigate("/products/new")} data-testid="btn-empty-add"><Plus className="w-4 h-4" /> Add Product</button>
                    </div>
                  </td></tr>
                ) : (
                  products.map((p) => {
                    const s = statusBadge(p);
                    return (
                      <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50/50 group" data-testid={`product-row-${p.id}`}>
                        <td className="agri-td">
                          <div className="w-10 h-10 rounded-lg bg-slate-100 overflow-hidden flex items-center justify-center">
                            {p.image_url ? <img src={p.image_url} alt="" className="w-full h-full object-cover" /> : <PackageSearch className="w-4 h-4 text-slate-400" />}
                          </div>
                        </td>
                        <td className="agri-td font-mono text-xs text-slate-500">{p.barcode || "-"}</td>
                        <td className="agri-td font-medium text-slate-800">{p.name}</td>
                        <td className="agri-td">{p.category || "-"}</td>
                        <td className="agri-td">{p.company || "-"}</td>
                        <td className="agri-td">{p.batch_number || "-"}</td>
                        <td className="agri-td">{fmtDate(p.manufacture_date)}</td>
                        <td className={`agri-td font-medium ${s.label === "Expired" ? "text-red-600" : s.label === "Expiring Soon" ? "text-amber-600" : "text-slate-700"}`}>{fmtDate(p.expiry_date)}</td>
                        <td className="agri-td font-semibold">{p.current_stock}</td>
                        <td className="agri-td">{p.unit}</td>
                        <td className="agri-td"><span className={`agri-badge ${s.cls}`}>{s.label}</span></td>
                        <td className="agri-td">
                          <div className="flex items-center gap-2">
                            <button onClick={() => navigate(`/products/${p.id}/edit`)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-agri-primary hover:text-agri-primary flex items-center justify-center transition-colors" data-testid={`btn-edit-${p.id}`}><Pencil className="w-3.5 h-3.5" /></button>
                            <button onClick={() => del(p)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center transition-colors" data-testid={`btn-delete-${p.id}`}><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          {products.length > 0 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-100 text-sm text-slate-500">
              <div>Showing <b className="text-slate-800">{products.length}</b> product{products.length !== 1 ? "s" : ""}</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
