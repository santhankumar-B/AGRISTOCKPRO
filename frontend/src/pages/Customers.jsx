import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency } from "@/lib/api";
import { Plus, Trash2, Pencil, X, Save, Users, Search } from "lucide-react";
import { toast } from "sonner";

const emptyForm = { name: "", phone: "", email: "", address: "", area: "", gst: "", credit_limit: 0, opening_balance: 0, status: "active" };

export default function Customers() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const load = () => api.get("/customers", { params: { q } }).then((r) => setRows(r.data));
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); /* eslint-disable-next-line */ }, [q]);

  const openNew = () => { setEditing(null); setForm(emptyForm); setShowForm(true); };
  const openEdit = (c) => { setEditing(c); setForm({ ...emptyForm, ...c }); setShowForm(true); };

  const submit = async (e) => {
    e.preventDefault();
    const payload = { ...form, credit_limit: Number(form.credit_limit), opening_balance: Number(form.opening_balance) };
    if (editing) { await api.put(`/customers/${editing.id}`, payload); toast.success("Customer updated"); }
    else { await api.post("/customers", payload); toast.success("Customer created"); }
    setShowForm(false); load();
  };

  const del = async (c) => { if (!window.confirm(`Delete ${c.name}?`)) return; await api.delete(`/customers/${c.id}`); toast.success("Deleted"); load(); };

  return (
    <>
      <Navbar title="Customers" subtitle="Manage your customer database and outstanding balances." />
      <div className="p-8 space-y-6">
        <div className="agri-card p-5 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[280px] relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input className="agri-input pl-10" placeholder="Search customer name, phone, email..." value={q} onChange={(e) => setQ(e.target.value)} data-testid="customer-search" />
          </div>
          <button className="agri-btn-primary" onClick={openNew} data-testid="btn-add-customer"><Plus className="w-4 h-4" /> Add Customer</button>
        </div>

        <div className="agri-card overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100"><tr>{["Name", "Phone", "Email", "Area", "GST", "Credit Limit", "Current Due", "Status", ""].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr></thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={9} className="p-16">
                  <div className="flex flex-col items-center text-center">
                    <Users className="w-14 h-14 text-slate-300 mb-3" />
                    <div className="font-poppins font-medium text-slate-800">No customers yet</div>
                    <div className="text-sm text-slate-500 mt-1 mb-5">Add your first customer.</div>
                    <button className="agri-btn-primary" onClick={openNew}><Plus className="w-4 h-4" /> Add Customer</button>
                  </div>
                </td></tr>
              ) : rows.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="agri-td font-medium text-slate-800">{c.name}</td>
                  <td className="agri-td">{c.phone || "-"}</td>
                  <td className="agri-td">{c.email || "-"}</td>
                  <td className="agri-td">{c.area || "-"}</td>
                  <td className="agri-td font-mono text-xs">{c.gst || "-"}</td>
                  <td className="agri-td">{fmtCurrency(c.credit_limit)}</td>
                  <td className="agri-td text-amber-600 font-medium">{fmtCurrency(c.current_due)}</td>
                  <td className="agri-td"><span className={`agri-badge ${c.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{c.status}</span></td>
                  <td className="agri-td">
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(c)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-agri-primary hover:text-agri-primary flex items-center justify-center"><Pencil className="w-3.5 h-3.5" /></button>
                      <button onClick={() => del(c)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center"><Trash2 className="w-3.5 h-3.5" /></button>
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
          <form onSubmit={submit} className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-poppins font-semibold text-xl text-slate-900">{editing ? "Edit" : "Add"} Customer</h3>
              <button type="button" onClick={() => setShowForm(false)} className="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center"><X className="w-4 h-4" /></button>
            </div>
            <div className="grid grid-cols-2 gap-5">
              <div><label className="agri-label">Name *</label><input required className="agri-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="cust-name" /></div>
              <div><label className="agri-label">Phone</label><input className="agri-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
              <div><label className="agri-label">Email</label><input className="agri-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
              <div><label className="agri-label">Area</label><input className="agri-input" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} /></div>
              <div className="col-span-2"><label className="agri-label">Address</label><textarea rows={2} className="agri-input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
              <div><label className="agri-label">GST No.</label><input className="agri-input" value={form.gst} onChange={(e) => setForm({ ...form, gst: e.target.value })} /></div>
              <div><label className="agri-label">Status</label><select className="agri-input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="active">active</option><option value="inactive">inactive</option></select></div>
              <div><label className="agri-label">Credit Limit</label><input type="number" className="agri-input" value={form.credit_limit} onChange={(e) => setForm({ ...form, credit_limit: e.target.value })} /></div>
              <div><label className="agri-label">Opening Balance</label><input type="number" className="agri-input" value={form.opening_balance} onChange={(e) => setForm({ ...form, opening_balance: e.target.value })} /></div>
            </div>
            <div className="flex justify-end gap-3 mt-6"><button type="button" className="agri-btn-secondary" onClick={() => setShowForm(false)}>Cancel</button><button type="submit" className="agri-btn-primary"><Save className="w-4 h-4" /> Save</button></div>
          </form>
        </div>
      )}
    </>
  );
}
