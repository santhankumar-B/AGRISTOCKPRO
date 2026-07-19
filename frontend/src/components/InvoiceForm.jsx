import { useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency, todayISO } from "@/lib/api";
import { useNavigate, useParams } from "react-router-dom";
import { Plus, Trash2, Search, Save, X, ClipboardList, ReceiptText, ChevronDown, UserPlus, Sparkles } from "lucide-react";
import { toast } from "sonner";
import InvoiceScannerModal from "@/components/InvoiceScannerModal";

/**
 * Reusable Invoice Form for Purchase & Sale
 * mode: "purchase" | "sale"
 */
export default function InvoiceForm({ mode = "purchase" }) {
  const isPurchase = mode === "purchase";
  const navigate = useNavigate();
  const { id } = useParams();

  const [products, setProducts] = useState([]);
  const [parties, setParties] = useState([]); // suppliers or customers
  const [productSearch, setProductSearch] = useState("");
  const [showProductList, setShowProductList] = useState(false);
  const [showPartyList, setShowPartyList] = useState(false);
  const [showScanner, setShowScanner] = useState(false);

  const [invoice, setInvoice] = useState(() => ({
    party_id: "",
    party_name: "",
    party_mobile: "",
    billing_address: "",
    invoice_number: "",
    invoice_date: todayISO(),
    due_date: todayISO(),
    delivery_date: todayISO(),
    warehouse: "Main Warehouse",
    reference_number: "",
    transporter: "",
    payment_terms: isPurchase ? "Credit (30 Days)" : "Cash",
    payment_method: "Cash",
    sales_person: "",
    sales_type: "Direct Sale",
    notes: "",
    items: [],
    discount_amount: 0,
    tax_default: isPurchase ? 5 : 0,
    received_amount: 0,
  }));

  useEffect(() => {
    api.get("/products").then((r) => setProducts(r.data));
    api.get(isPurchase ? "/suppliers" : "/customers").then((r) => setParties(r.data));
    if (id) {
      api.get(isPurchase ? `/purchases/${id}` : `/sales/${id}`).then((r) => {
        const d = r.data;
        setInvoice({
          party_id: isPurchase ? d.supplier_id : d.customer_id,
          party_name: isPurchase ? (d.supplier_name || "") : (d.customer_name || ""),
          party_mobile: d.customer_mobile || "",
          billing_address: d.billing_address || "",
          invoice_number: d.invoice_number || "",
          invoice_date: d.invoice_date || todayISO(),
          due_date: d.due_date || todayISO(),
          delivery_date: d.delivery_date || todayISO(),
          warehouse: d.warehouse || "Main Warehouse",
          reference_number: d.reference_number || "",
          transporter: d.transporter || "",
          payment_terms: d.payment_terms || "",
          payment_method: d.payment_method || "Cash",
          sales_person: d.sales_person || "",
          sales_type: d.sales_type || "Direct Sale",
          notes: d.notes || "",
          items: d.items || [],
          discount_amount: d.discount || 0,
          tax_default: isPurchase ? 5 : 0,
          received_amount: isPurchase ? (d.paid_amount || 0) : (d.received_amount || 0),
        });
      });
    } else {
      api.get("/meta/next-invoice", { params: { kind: isPurchase ? "purchase" : "sale" } })
        .then((r) => setInvoice((v) => ({ ...v, invoice_number: r.data.number, tax_default: isPurchase ? 5 : 0 })));
    }
  }, [isPurchase, id]);

  const totals = useMemo(() => {
    const subtotal = invoice.items.reduce((s, it) => s + (Number(it.qty) * Number(it.unit_price)) * (1 - Number(it.discount_percent || 0) / 100), 0);
    const tax = invoice.items.reduce((s, it) => {
      const base = Number(it.qty) * Number(it.unit_price) * (1 - Number(it.discount_percent || 0) / 100);
      return s + base * (Number(it.tax_percent || 0) / 100);
    }, 0);
    const cgst = tax / 2;
    const sgst = tax / 2;
    const total = subtotal + tax - Number(invoice.discount_amount || 0);
    return { subtotal, cgst, sgst, total };
  }, [invoice.items, invoice.discount_amount]);

  const addProduct = (p) => {
    setInvoice((v) => ({
      ...v,
      items: [...v.items, {
        product_id: p.id,
        product_name: p.name,
        barcode: p.barcode || "",
        batch_number: p.batch_number || "",
        manufacture_date: p.manufacture_date || "",
        expiry_date: p.expiry_date || "",
        unit: p.unit || "",
        qty: 1,
        unit_price: isPurchase ? Number(p.purchase_price || 0) : Number(p.selling_price || 0),
        discount_percent: 0,
        tax_percent: typeof v.tax_default === "number" ? v.tax_default : (isPurchase ? 5 : 0),
        amount: 0,
      }],
    }));
    setShowProductList(false);
    setProductSearch("");
  };

  const updateItem = (idx, key, value) => {
    setInvoice((v) => {
      const items = [...v.items];
      items[idx] = { ...items[idx], [key]: value };
      const it = items[idx];
      const base = Number(it.qty) * Number(it.unit_price) * (1 - Number(it.discount_percent || 0) / 100);
      items[idx].amount = base * (1 + Number(it.tax_percent || 0) / 100);
      return { ...v, items };
    });
  };

  const removeItem = (idx) => setInvoice((v) => ({ ...v, items: v.items.filter((_, i) => i !== idx) }));

  const chooseParty = (id) => {
    const p = parties.find((x) => x.id === id);
    if (!p) return setInvoice((v) => ({ ...v, party_id: "", party_name: "" }));
    setInvoice((v) => ({
      ...v, party_id: p.id, party_name: p.name,
      party_mobile: p.phone || "",
      billing_address: p.address || "",
    }));
  };

  const submit = async (status = "posted") => {
    if (!invoice.party_name.trim()) {
      return toast.error(`Please enter or select a ${isPurchase ? "supplier" : "customer"}`);
    }
    if (invoice.items.length === 0) return toast.error("Add at least one product");

    let partyId = invoice.party_id;
    let partyName = invoice.party_name.trim();

    // Auto-create customer or supplier if new and not selected
    if (!partyId) {
      const existing = parties.find((p) => p.name.toLowerCase() === partyName.toLowerCase());
      if (existing) {
        partyId = existing.id;
      } else {
        try {
          const res = await api.post(isPurchase ? "/suppliers" : "/customers", isPurchase ? {
            name: partyName, phone: invoice.party_mobile || "", address: invoice.billing_address || "",
          } : {
            name: partyName, phone: invoice.party_mobile || "", address: invoice.billing_address || "",
          });
          partyId = res.data.id;
          toast.success(`New ${isPurchase ? "supplier" : "customer"} "${partyName}" added to directory`);
        } catch (e) {
          console.warn("Auto-create party error:", e);
        }
      }
    }

    const payload = isPurchase ? {
      supplier_id: partyId, supplier_name: partyName,
      invoice_number: invoice.invoice_number, invoice_date: invoice.invoice_date,
      warehouse: invoice.warehouse, reference_number: invoice.reference_number,
      transporter: invoice.transporter, payment_terms: invoice.payment_terms,
      delivery_date: invoice.delivery_date, notes: invoice.notes,
      items: invoice.items, subtotal: totals.subtotal, discount: Number(invoice.discount_amount || 0),
      cgst: totals.cgst, sgst: totals.sgst, total: totals.total,
      paid_amount: Number(invoice.received_amount || 0),
      due_amount: totals.total - Number(invoice.received_amount || 0),
      payment_method: invoice.payment_method, status,
    } : {
      customer_id: partyId, customer_name: partyName,
      customer_mobile: invoice.party_mobile, billing_address: invoice.billing_address,
      invoice_number: invoice.invoice_number, invoice_date: invoice.invoice_date,
      due_date: invoice.due_date, sales_person: invoice.sales_person,
      sales_type: invoice.sales_type, payment_terms: invoice.payment_terms,
      notes: invoice.notes, items: invoice.items, subtotal: totals.subtotal,
      discount: Number(invoice.discount_amount || 0), cgst: totals.cgst, sgst: totals.sgst,
      total: totals.total, received_amount: Number(invoice.received_amount || 0),
      change_amount: Math.max(0, Number(invoice.received_amount || 0) - totals.total),
      payment_method: invoice.payment_method, status,
    };
    try {
      if (id) {
        await api.put(isPurchase ? `/purchases/${id}` : `/sales/${id}`, payload);
        toast.success(`${isPurchase ? "Purchase" : "Sale"} updated`);
      } else {
        await api.post(isPurchase ? "/purchases" : "/sales", payload);
        toast.success(`${isPurchase ? "Purchase" : "Sale"} ${status === "draft" ? "saved as draft" : "saved"}`);
      }
      navigate(isPurchase ? "/purchase" : "/sales");
    } catch (e) {
      toast.error(id ? "Update failed" : "Save failed");
    }
  };

  const filteredProducts = products.filter((p) => {
    if (!productSearch) return true;
    const s = productSearch.toLowerCase();
    return p.name.toLowerCase().includes(s) || (p.barcode || "").toLowerCase().includes(s);
  }).slice(0, 8);

  const filteredParties = parties.filter((p) => {
    if (!invoice.party_name) return true;
    return p.name.toLowerCase().includes(invoice.party_name.toLowerCase());
  }).slice(0, 8);

  return (
    <>
      <Navbar title={id ? (isPurchase ? "Edit Purchase" : "Edit Sale") : (isPurchase ? "Purchase Entry" : "Sales Entry")} subtitle={`Dashboard / ${isPurchase ? "Purchase" : "Sales"} / ${id ? "Edit" : "Add"}`} />
      <div className="p-8 grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="agri-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-agri-primary" />
                <h3 className="font-poppins font-semibold text-lg text-slate-900">{isPurchase ? "Purchase" : "Customer & Invoice"} Details</h3>
              </div>
              {isPurchase && !id && (
                <button
                  type="button"
                  onClick={() => setShowScanner(true)}
                  className="bg-emerald-700 hover:bg-emerald-800 text-white font-medium text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-lime-300" /> 📸 Auto-Fill from Paper Photo (AI)
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
              <div className="md:col-span-2 relative">
                <label className="agri-label">{isPurchase ? "Supplier" : "Customer"} Name <span className="text-red-500">*</span></label>
                <div className="relative">
                  <input
                    className="agri-input pr-8"
                    placeholder={`Enter or type ${isPurchase ? "supplier" : "customer"} name...`}
                    value={invoice.party_name}
                    onChange={(e) => {
                      const val = e.target.value;
                      const matched = parties.find((p) => p.name.toLowerCase() === val.toLowerCase());
                      setInvoice((v) => ({
                        ...v,
                        party_name: val,
                        party_id: matched ? matched.id : "",
                        party_mobile: matched ? (matched.phone || v.party_mobile) : v.party_mobile,
                        billing_address: matched ? (matched.address || v.billing_address) : v.billing_address,
                      }));
                      setShowPartyList(true);
                    }}
                    onFocus={() => setShowPartyList(true)}
                    onBlur={() => setTimeout(() => setShowPartyList(false), 200)}
                    data-testid="party-name-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPartyList(!showPartyList)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>

                {showPartyList && (
                  <div className="absolute z-20 top-full mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-dropdown max-h-60 overflow-auto">
                    {filteredParties.length === 0 ? (
                      <div className="p-3 text-xs text-amber-700 bg-amber-50 flex items-center gap-2">
                        <UserPlus className="w-4 h-4 text-amber-600 shrink-0" />
                        <span>"{invoice.party_name}" not found. Will be added automatically to {isPurchase ? "Suppliers" : "Customers"} directory.</span>
                      </div>
                    ) : (
                      filteredParties.map((p) => (
                        <button
                          type="button"
                          key={p.id}
                          onClick={() => {
                            chooseParty(p.id);
                            setShowPartyList(false);
                          }}
                          className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-slate-50 border-b border-slate-50 last:border-0 text-left"
                        >
                          <div>
                            <div className="text-sm font-medium text-slate-800">{p.name}</div>
                            {p.phone && <div className="text-xs text-slate-400">{p.phone}</div>}
                          </div>
                          {!isPurchase && p.current_due > 0 && (
                            <span className="text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                              Due: {fmtCurrency(p.current_due)}
                            </span>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div>
                <label className="agri-label">Invoice No. <span className="text-red-500">*</span></label>
                <input className="agri-input" value={invoice.invoice_number} onChange={(e) => setInvoice({ ...invoice, invoice_number: e.target.value })} data-testid="invoice-number" />
              </div>
              <div>
                <label className="agri-label">Invoice Date <span className="text-red-500">*</span></label>
                <input type="date" className="agri-input" value={invoice.invoice_date} onChange={(e) => setInvoice({ ...invoice, invoice_date: e.target.value })} />
              </div>

              {isPurchase ? (
                <>
                  <div><label className="agri-label">Payment Terms</label>
                    <select className="agri-input" value={invoice.payment_terms} onChange={(e) => setInvoice({ ...invoice, payment_terms: e.target.value })}>
                      {["Cash", "Credit (15 Days)", "Credit (30 Days)", "Credit (60 Days)"].map((o) => <option key={o}>{o}</option>)}
                    </select></div>
                  <div><label className="agri-label">Delivery Date</label>
                    <input type="date" className="agri-input" value={invoice.delivery_date} onChange={(e) => setInvoice({ ...invoice, delivery_date: e.target.value })} /></div>
                  <div><label className="agri-label">Reference No.</label>
                    <input className="agri-input" value={invoice.reference_number} onChange={(e) => setInvoice({ ...invoice, reference_number: e.target.value })} /></div>
                  <div><label className="agri-label">Transporter</label>
                    <input className="agri-input" value={invoice.transporter} onChange={(e) => setInvoice({ ...invoice, transporter: e.target.value })} /></div>
                  <div><label className="agri-label">Warehouse</label>
                    <select className="agri-input" value={invoice.warehouse} onChange={(e) => setInvoice({ ...invoice, warehouse: e.target.value })}>
                      {["Main Warehouse", "Secondary", "Cold Storage"].map((o) => <option key={o}>{o}</option>)}
                    </select></div>
                </>
              ) : (
                <>
                  <div><label className="agri-label">Mobile</label>
                    <input className="agri-input" value={invoice.party_mobile} onChange={(e) => setInvoice({ ...invoice, party_mobile: e.target.value })} /></div>
                  <div><label className="agri-label">Payment Terms</label>
                    <select className="agri-input" value={invoice.payment_terms} onChange={(e) => setInvoice({ ...invoice, payment_terms: e.target.value })}>
                      {["Cash", "Credit", "Card", "UPI"].map((o) => <option key={o}>{o}</option>)}
                    </select></div>
                  <div><label className="agri-label">Due Date</label>
                    <input type="date" className="agri-input" value={invoice.due_date} onChange={(e) => setInvoice({ ...invoice, due_date: e.target.value })} /></div>
                  <div><label className="agri-label">Sales Person</label>
                    <input className="agri-input" value={invoice.sales_person} onChange={(e) => setInvoice({ ...invoice, sales_person: e.target.value })} /></div>
                </>
              )}

              <div className="md:col-span-2">
                <label className="agri-label">{isPurchase ? "Notes" : "Billing Address"}</label>
                {isPurchase ? (
                  <input className="agri-input" placeholder="Notes (optional)..." value={invoice.notes} onChange={(e) => setInvoice({ ...invoice, notes: e.target.value })} />
                ) : (
                  <textarea rows={2} className="agri-input" value={invoice.billing_address} onChange={(e) => setInvoice({ ...invoice, billing_address: e.target.value })} />
                )}
              </div>
              {!isPurchase && (
                <div className="md:col-span-2"><label className="agri-label">Notes (Optional)</label>
                  <input className="agri-input" value={invoice.notes} onChange={(e) => setInvoice({ ...invoice, notes: e.target.value })} /></div>
              )}
            </div>
          </div>

          {/* Line Items */}
          <div className="agri-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-poppins font-semibold text-lg text-slate-900">Add Products</h3>
              <div className="text-xs text-slate-500">Default Tax %:
                <input type="number" className="w-14 ml-2 border border-slate-200 rounded px-2 py-1 text-sm" value={invoice.tax_default} onChange={(e) => setInvoice({ ...invoice, tax_default: Number(e.target.value) })} />
              </div>
            </div>
            <div className="relative mb-3">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input className="agri-input pl-10" placeholder="Search product by name or barcode..." value={productSearch} onFocus={() => setShowProductList(true)} onBlur={() => setTimeout(() => setShowProductList(false), 200)} onChange={(e) => { setProductSearch(e.target.value); setShowProductList(true); }} data-testid="product-search-invoice" />
              {showProductList && productSearch && (
                <div className="absolute z-20 top-full mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-dropdown max-h-80 overflow-auto">
                  {filteredProducts.length === 0 && <div className="p-4 text-sm text-slate-400">No products found</div>}
                  {filteredProducts.map((p) => (
                    <button type="button" key={p.id} onClick={() => addProduct(p)} className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 border-b border-slate-50 last:border-0 text-left">
                      <div>
                        <div className="text-sm font-medium text-slate-800">{p.name}</div>
                        <div className="text-xs text-slate-500">{p.barcode || "no barcode"} • Stock: {p.current_stock} {p.unit}</div>
                      </div>
                      <div className="text-sm font-semibold text-agri-primary">{fmtCurrency(isPurchase ? p.purchase_price : p.selling_price)}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-slate-200">
                  <tr>{["#", "Product", "Batch", "Expiry", "Unit", "Qty", "Rate", "Disc %", "Tax %", "Amount", ""].map((h) => <th key={h} className="agri-th">{h}</th>)}</tr>
                </thead>
                <tbody>
                  {invoice.items.map((it, i) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="agri-td text-slate-400">{i + 1}</td>
                      <td className="agri-td min-w-[180px]">
                        <div className="font-medium text-slate-800">{it.product_name}</div>
                        <div className="text-xs text-slate-500 font-mono">{it.barcode}</div>
                      </td>
                      <td className="agri-td">{it.batch_number || "-"}</td>
                      <td className="agri-td">{it.expiry_date || "-"}</td>
                      <td className="agri-td">{it.unit}</td>
                      <td className="agri-td"><input type="number" min="0" className="w-20 border border-slate-200 rounded-lg px-2 py-1 text-sm" value={it.qty} onChange={(e) => updateItem(i, "qty", Number(e.target.value))} /></td>
                      <td className="agri-td"><input type="number" min="0" className="w-24 border border-slate-200 rounded-lg px-2 py-1 text-sm" value={it.unit_price} onChange={(e) => updateItem(i, "unit_price", Number(e.target.value))} /></td>
                      <td className="agri-td"><input type="number" min="0" className="w-16 border border-slate-200 rounded-lg px-2 py-1 text-sm" value={it.discount_percent} onChange={(e) => updateItem(i, "discount_percent", Number(e.target.value))} /></td>
                      <td className="agri-td"><input type="number" min="0" className="w-16 border border-slate-200 rounded-lg px-2 py-1 text-sm" value={it.tax_percent} onChange={(e) => updateItem(i, "tax_percent", Number(e.target.value))} /></td>
                      <td className="agri-td font-semibold">{fmtCurrency(it.amount)}</td>
                      <td className="agri-td"><button onClick={() => removeItem(i)} className="w-8 h-8 rounded-lg border border-slate-200 hover:border-red-400 hover:text-red-500 flex items-center justify-center transition-colors"><Trash2 className="w-3.5 h-3.5" /></button></td>
                    </tr>
                  ))}
                  {invoice.items.length === 0 && (
                    <tr><td colSpan={11} className="p-10 text-center text-sm text-slate-400">Search & select products above to add line items</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="space-y-6">
          <div className="agri-card p-6 sticky top-24">
            <div className="flex items-center gap-2 mb-4">
              <ReceiptText className="w-5 h-5 text-agri-primary" />
              <h3 className="font-poppins font-semibold text-lg text-slate-900">Summary</h3>
            </div>
            <div className="space-y-2.5 text-sm">
              <Row label="Subtotal" value={fmtCurrency(totals.subtotal)} />
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Discount</span>
                <input type="number" className="w-24 text-right border border-slate-200 rounded-lg px-2 py-1 text-sm" value={invoice.discount_amount} onChange={(e) => setInvoice({ ...invoice, discount_amount: Number(e.target.value) })} />
              </div>
              <Row label="CGST" value={fmtCurrency(totals.cgst)} />
              <Row label="SGST" value={fmtCurrency(totals.sgst)} />
              <div className="border-t border-slate-100 pt-3 mt-3 flex justify-between items-center">
                <span className="font-poppins font-semibold text-slate-900">Total</span>
                <span className="font-poppins font-bold text-xl text-agri-primary" data-testid="total-amount">{fmtCurrency(totals.total)}</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <div>
                <label className="agri-label">Payment Method</label>
                <select className="agri-input" value={invoice.payment_method} onChange={(e) => setInvoice({ ...invoice, payment_method: e.target.value })}>
                  {["Cash", "UPI", "Card", "Bank Transfer", "Cheque"].map((o) => <option key={o}>{o}</option>)}
                </select>
              </div>
              <div>
                <label className="agri-label">{isPurchase ? "Paid" : "Received"} Amount</label>
                <input type="number" className="agri-input" value={invoice.received_amount} onChange={(e) => setInvoice({ ...invoice, received_amount: Number(e.target.value) })} data-testid="received-amount" />
              </div>
              <div>
                <label className="agri-label">{isPurchase ? "Due" : "Change"} Amount</label>
                <input readOnly className="agri-input bg-slate-100"
                       value={fmtCurrency(isPurchase ? Math.max(0, totals.total - Number(invoice.received_amount || 0)) : Math.max(0, Number(invoice.received_amount || 0) - totals.total))} />
              </div>
            </div>

            <div className="mt-6 space-y-2">
              <button onClick={() => submit("posted")} className="agri-btn-primary w-full" data-testid="btn-save-posted">
                <Save className="w-4 h-4" /> {id ? (isPurchase ? "Update Purchase" : "Update Sale") : (isPurchase ? "Save Purchase" : "Save & Print Invoice")}
              </button>
              <button onClick={() => submit("draft")} className="agri-btn-secondary w-full" data-testid="btn-save-draft">Save as Draft</button>
              <button onClick={() => navigate(-1)} className="agri-btn-ghost w-full justify-center"><X className="w-4 h-4" /> Cancel</button>
            </div>
          </div>
        </div>
      </div>
      <InvoiceScannerModal isOpen={showScanner} onClose={() => setShowScanner(false)} onSuccess={() => navigate("/purchase")} />
    </>
  );
}

const Row = ({ label, value }) => (
  <div className="flex justify-between text-slate-600"><span>{label}</span><span className="font-medium text-slate-800">{value}</span></div>
);
