import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency } from "@/lib/api";
import { Plus, Trash2, Pencil, X, Save, Building2, Search } from "lucide-react";
import { toast } from "sonner";

const emptyForm = { name: "", company: "", phone: "", email: "", address: "", gst: "", bank_name: "", bank_account: "", ifsc: "", opening_balance: 0, status: "active" };

export default function Suppliers() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const load = () => api.get("/suppliers", { params: { q } }).then((r) => setRows(r.data));
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); /* eslint-disable-next-line */ }, [q]);

  const openNew = () => { setEditing(null); setForm(emptyForm); setShowForm(true); };
  const openEdit = (s) => { setEditing(s); setForm({ ...emptyForm, ...s }); setShowForm(true); };

  const submit = async (e) => {
    e.preventDefault();
    const payload = { ...form, opening_balance: Number(form.opening_balance) };
    if (editing) { await api.put(`/suppliers/${editing.id}`, payload); toast.success("Supplier updated"); }
    else { await api.post("/suppliers", payload); toast.success("Supplier created"); }
    setShowForm(false); load();
  };

  const del = async (s) => { if (!window.confirm(`Delete ${s.name}?`)) return; await api.delete(`/suppliers/${s.id}`); toast.success("Deleted"); load(); };

  return (
    <>
      <Navbar title="Suppliers" subtitle="Manage your supplier network and outstanding payables." />
      <div className="p-8 space-y-6">
        <div className="agri-card p-5 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[280px] relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input className="agri-input pl-10" placeholder="Search supplier..." value={q} onChange={(e) => setQ(e.target.value)} data-testid="supplier-search" />
          </div>
          <button className="agri-btn-primary" onClick={openNew} data-testid="btn-add-supplier"><Plus className="w-4 h-4" /> Add Supplier</button>
        </div>

        <div className="agri-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100"><tr>{["Name", "Company", "Phone", "Email", "GST", "Bank", "Outstanding", "Status", ""].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr></thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={9} className="p-16">
                  <div className="flex flex-col items-center text-center">
                    <Building2 className="w-14 h-14 text-slate-300 mb-3" />
                    <div className="font-poppins font-medium text-slate-800">No suppliers yet</div>
                    <div className="text-sm text-slate-500 mt-1 mb-5">Add your first supplier.</div>
                    <button className="agri-btn-primary" onClick={openNew}><Plus className="w-4 h-4" /> Add Supplier</button>
                  </div>
                </td></tr>
              ) : rows.map((s) => (
                <tr key={s.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="agri-td font-medium text-slate-800">{s.name}</td>
                  <td className="agri-td">{s.company || "-"}</td>
                  <td className="agri-td">{s.phone || "-"}</td>
                  <td className="agri-td">{s.email || "-"}</td>
                  <td className="agri-td font-mono text-xs">{s.gst || "-"}</td>
                  <td className="agri-td">{s.bank_name || "-"}</td>
                  <td className="agri-td text-amber-600 font-medium">{fmtCurrency(s.outstanding_amount)}</td>
                  <td className="agri-td"><span className={`agri-badge ${s.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{s.status}</span></td>
                  <td className="agri-td">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(s)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-agri-primary hover:text-agri-primary flex items-center justify-center"><Pencil className="w-3.5 h-3.5" /></button>
                      <button onClick={() => del(s)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <form onSubmit={submit} className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-poppins font-semibold text-xl text-slate-900">{editing ? "Edit" : "Add"} Supplier</h3>
              <button type="button" onClick={() => setShowForm(false)} className="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center"><X className="w-4 h-4" /></button>
            </div>
            <div className="grid grid-cols-3 gap-5">
              <div><label className="agri-label">Name *</label><input required className="agri-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="sup-name" /></div>
              <div><label className="agri-label">Company</label><input className="agri-input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></div>
              <div><label className="agri-label">Phone</label><input className="agri-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
              <div><label className="agri-label">Email</label><input className="agri-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
              <div><label className="agri-label">GST</label><input className="agri-input" value={form.gst} onChange={(e) => setForm({ ...form, gst: e.target.value })} /></div>
              <div><label className="agri-label">Opening Balance</label><input type="number" className="agri-input" value={form.opening_balance} onChange={(e) => setForm({ ...form, opening_balance: e.target.value })} /></div>
              <div className="col-span-3"><label className="agri-label">Address</label><textarea rows={2} className="agri-input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
              <div><label className="agri-label">Bank Name</label><input className="agri-input" value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} /></div>
              <div><label className="agri-label">Account No.</label><input className="agri-input" value={form.bank_account} onChange={(e) => setForm({ ...form, bank_account: e.target.value })} /></div>
              <div><label className="agri-label">IFSC</label><input className="agri-input" value={form.ifsc} onChange={(e) => setForm({ ...form, ifsc: e.target.value })} /></div>
            </div>
            <div className="flex justify-end gap-3 mt-6"><button type="button" className="agri-btn-secondary" onClick={() => setShowForm(false)}>Cancel</button><button type="submit" className="agri-btn-primary"><Save className="w-4 h-4" /> Save</button></div>
          </form>
        </div>
      )}
    </>
  );
}
