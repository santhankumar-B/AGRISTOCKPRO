import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api from "@/lib/api";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ChevronLeft, Save, RotateCcw, X } from "lucide-react";
import { toast } from "sonner";

const emptyForm = {
  name: "", category: "", company: "", brand: "", barcode: "",
  batch_number: "", manufacture_date: "", expiry_date: "", unit: "Bag",
  purchase_price: 0, selling_price: 0, opening_stock: 0, minimum_stock: 0,
  rack_number: "", image_url: "", description: "",
};

const Field = ({ label, k, value, onChange, type = "text", options, required }) => (
  <div>
    <label className="agri-label">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
    {options ? (
      <select className="agri-input" value={value} onChange={(e) => onChange(k, e.target.value)} data-testid={`field-${k}`}>
        {options.map((o) => <option key={o} value={o}>{o || "— Select —"}</option>)}
      </select>
    ) : type === "textarea" ? (
      <textarea rows={3} className="agri-input" value={value} onChange={(e) => onChange(k, e.target.value)} data-testid={`field-${k}`} />
    ) : (
      <input type={type} className="agri-input" value={value} onChange={(e) => onChange(k, e.target.value)} required={required} data-testid={`field-${k}`} />
    )}
  </div>
);

export default function ProductForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      api.get(`/products/${id}`).then((r) => {
        const p = r.data;
        setForm({ ...emptyForm, ...p, opening_stock: p.current_stock });
      });
    }
  }, [id]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        purchase_price: Number(form.purchase_price),
        selling_price: Number(form.selling_price),
        opening_stock: Number(form.opening_stock),
        minimum_stock: Number(form.minimum_stock),
      };
      if (id) { await api.put(`/products/${id}`, payload); toast.success("Product updated"); }
      else { await api.post("/products", payload); toast.success("Product created"); }
      navigate("/products");
    } catch {
      toast.error("Save failed");
    } finally { setSaving(false); }
  };

  return (
    <>
      <Navbar title={id ? "Edit Product" : "Add Product"} subtitle="Dashboard / Products / Add" />
      <div className="p-8">
        <form onSubmit={submit} className="agri-card p-8 space-y-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Link to="/products" className="agri-btn-ghost"><ChevronLeft className="w-4 h-4" /> Back</Link>
            </div>
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Field label="Product Name" k="name" value={form.name} onChange={set} required />
              <Field label="Category" k="category" value={form.category} onChange={set} options={["", "Fertilizers", "Seeds", "Pesticides", "Herbicides", "Tools", "Others"]} />
              <Field label="Company" k="company" value={form.company} onChange={set} />
              <Field label="Brand" k="brand" value={form.brand} onChange={set} />
              <Field label="Barcode" k="barcode" value={form.barcode} onChange={set} />
              <Field label="Batch Number" k="batch_number" value={form.batch_number} onChange={set} />
              <Field label="Manufacture Date" k="manufacture_date" value={form.manufacture_date} onChange={set} type="date" />
              <Field label="Expiry Date" k="expiry_date" value={form.expiry_date} onChange={set} type="date" />
              <Field label="Unit" k="unit" value={form.unit} onChange={set} options={["Bag", "Bottle", "Packet", "Kg", "Litre", "Piece", "Box"]} />
            </div>
          </div>

          <div>
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Pricing & Stock</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Field label="Purchase Price (₹)" k="purchase_price" value={form.purchase_price} onChange={set} type="number" />
              <Field label="Selling Price (₹)" k="selling_price" value={form.selling_price} onChange={set} type="number" />
              <Field label="Opening Stock" k="opening_stock" value={form.opening_stock} onChange={set} type="number" />
              <Field label="Minimum Stock" k="minimum_stock" value={form.minimum_stock} onChange={set} type="number" />
              <Field label="Rack Number" k="rack_number" value={form.rack_number} onChange={set} />
              <Field label="Image URL" k="image_url" value={form.image_url} onChange={set} />
            </div>
          </div>

          <div>
            <Field label="Description" k="description" value={form.description} onChange={set} type="textarea" />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" className="agri-btn-secondary" onClick={() => navigate("/products")} data-testid="btn-cancel"><X className="w-4 h-4" /> Cancel</button>
            <button type="button" className="agri-btn-secondary" onClick={() => setForm(emptyForm)} data-testid="btn-reset"><RotateCcw className="w-4 h-4" /> Reset</button>
            <button type="submit" disabled={saving} className="agri-btn-primary" data-testid="btn-save"><Save className="w-4 h-4" /> {saving ? "Saving..." : "Save Product"}</button>
          </div>
        </form>
      </div>
    </>
  );
}
