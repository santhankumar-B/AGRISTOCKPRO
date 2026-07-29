import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Camera, Check, X, Sparkles, Loader2, FileText, Plus, Trash2, ArrowRight } from "lucide-react";
import api, { fmtCurrency, todayISO } from "@/lib/api";
import { toast } from "sonner";

export default function InvoiceScannerModal({ isOpen, onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [extracted, setExtracted] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setExtracted(null);
  };

  const handleScan = async () => {
    if (!file) {
      toast.error("Please select or upload an invoice image first");
      return;
    }
    setScanning(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/purchases/scan-invoice", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setExtracted(data.extracted);
      toast.success("Invoice analyzed successfully!");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to analyze invoice photo");
    } finally {
      setScanning(false);
    }
  };

  const recalculateTotals = (items, discount = 0, cgst = 0, sgst = 0) => {
    const subtotal = items.reduce((sum, item) => sum + (Number(item.qty || 0) * Number(item.unit_price || 0)), 0);
    const taxTotal = (Number(cgst || 0) + Number(sgst || 0));
    const total = Math.max(0, subtotal + taxTotal - Number(discount || 0));
    return { subtotal, total };
  };

  const updateExtractedField = (field, val) => {
    setExtracted((v) => {
      const updated = { ...v, [field]: val };
      if (field === "discount" || field === "cgst" || field === "sgst") {
        const { subtotal, total } = recalculateTotals(updated.items, updated.discount, updated.cgst, updated.sgst);
        updated.subtotal = subtotal;
        updated.total = total;
      }
      return updated;
    });
  };

  const updateItemField = (idx, field, val) => {
    setExtracted((v) => {
      const items = [...v.items];
      const item = { ...items[idx], [field]: val };
      if (field === "qty" || field === "unit_price") {
        item.amount = Number(item.qty || 0) * Number(item.unit_price || 0);
      }
      items[idx] = item;
      const { subtotal, total } = recalculateTotals(items, v.discount, v.cgst, v.sgst);
      return { ...v, items, subtotal, total };
    });
  };

  const addItem = () => {
    setExtracted((v) => {
      const items = [
        ...v.items,
        {
          product_name: "New Product",
          category: "General",
          batch_number: "",
          expiry_date: "",
          unit: "Unit",
          qty: 1,
          unit_price: 0,
          discount_percent: 0,
          tax_percent: 5,
          amount: 0,
        },
      ];
      const { subtotal, total } = recalculateTotals(items, v.discount, v.cgst, v.sgst);
      return { ...v, items, subtotal, total };
    });
  };

  const removeItem = (idx) => {
    setExtracted((v) => {
      const items = v.items.filter((_, i) => i !== idx);
      const { subtotal, total } = recalculateTotals(items, v.discount, v.cgst, v.sgst);
      return { ...v, items, subtotal, total };
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && extracted && !saving) {
      e.preventDefault();
      handleSavePurchase();
    }
  };

  const handleSavePurchase = async () => {
    if (!extracted) return;
    setSaving(true);
    try {
      // 1. Ensure supplier exists
      const { data: suppliers } = await api.get("/suppliers", { params: { q: extracted.supplier_name } });
      let supplier_id = suppliers?.[0]?.id;
      if (!supplier_id && extracted.supplier_name) {
        const { data: newSup } = await api.post("/suppliers", {
          name: extracted.supplier_name,
          company: extracted.supplier_name,
          phone: extracted.supplier_phone || "",
          gst: extracted.supplier_gst || "",
          address: extracted.supplier_address || "",
        });
        supplier_id = newSup.id;
      }

      // 2. Ensure products exist
      const { data: allProds } = await api.get("/products");
      const prodMap = {};
      allProds.forEach((p) => { prodMap[p.name.toLowerCase()] = p; });

      const purchaseItems = [];
      for (const item of extracted.items) {
        const key = item.product_name.toLowerCase().trim();
        let pid = prodMap[key]?.id;
        if (!pid) {
          const { data: newProd } = await api.post("/products", {
            name: item.product_name,
            category: item.category || "General",
            unit: item.unit || "Unit",
            batch_number: item.batch_number || "",
            expiry_date: item.expiry_date || "",
            purchase_price: Number(item.unit_price || 0),
            selling_price: Number(item.unit_price || 0) * 1.15,
            opening_stock: Number(item.qty || 0),
          });
          pid = newProd.id;
        }

        purchaseItems.push({
          product_id: pid,
          product_name: item.product_name,
          unit: item.unit || "Unit",
          qty: Number(item.qty || 0),
          unit_price: Number(item.unit_price || 0),
          amount: Number(item.amount || (item.qty * item.unit_price)),
          batch_number: item.batch_number || "",
          expiry_date: item.expiry_date || "",
        });
      }

      // 3. Post Purchase Entry directly to purchase database
      const payload = {
        supplier_id: supplier_id || "",
        supplier_name: extracted.supplier_name || "Unknown Supplier",
        invoice_number: extracted.invoice_number || `INV-${Date.now().toString().slice(-6)}`,
        invoice_date: extracted.invoice_date || todayISO(),
        due_date: todayISO(),
        delivery_date: todayISO(),
        warehouse: "Main Warehouse",
        payment_terms: "Credit",
        payment_method: "Credit",
        items: purchaseItems,
        subtotal: Number(extracted.subtotal || 0),
        discount: Number(extracted.discount || 0),
        cgst: Number(extracted.cgst || 0),
        sgst: Number(extracted.sgst || 0),
        total: Number(extracted.total || 0),
        paid_amount: 0,
        due_amount: Number(extracted.total || 0),
        status: "posted",
        notes: "Auto-scanned from paper invoice photo",
      };

      await api.post("/purchases", payload);
      toast.success("Purchase entry saved directly into database!");
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to save scanned purchase");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden"
          onKeyDown={handleKeyDown}
        >
          {/* Header */}
          <div className="p-6 bg-gradient-to-r from-[#0F3D1F] to-[#15803D] text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="w-5 h-5 text-lime-300" />
              </div>
              <div>
                <h2 className="font-poppins font-bold text-xl">Automated Invoice Scanning & Expense Tracking</h2>
                <p className="text-xs text-white/80">Upload bill photo/PDF -> Review extracted fields -> Press Enter to Confirm & Save</p>
              </div>
            </div>
            <button onClick={onClose} className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto flex-1 space-y-6">
            {!extracted ? (
              <div className="space-y-6">
                {/* File Dropzone */}
                <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 flex flex-col items-center justify-center bg-slate-50 hover:bg-slate-100/80 transition-colors text-center cursor-pointer relative">
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  {preview ? (
                    <div className="relative max-h-64 overflow-hidden rounded-xl border border-slate-200">
                      <img src={preview} alt="Invoice paper preview" className="object-contain max-h-64" />
                    </div>
                  ) : (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-green-100 text-green-700 flex items-center justify-center mb-3">
                        <Camera className="w-7 h-7" />
                      </div>
                      <h3 className="font-poppins font-semibold text-slate-800 text-base">Upload or Scan Invoice / Purchase Bill</h3>
                      <p className="text-xs text-slate-500 mt-1 max-w-sm">Supports JPG, PNG, WEBP images or scanned PDF purchase bills</p>
                    </>
                  )}
                </div>

                <div className="flex justify-end gap-3">
                  <button type="button" onClick={onClose} className="agri-btn-secondary py-2.5">
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleScan}
                    disabled={!file || scanning}
                    className="agri-btn-primary py-2.5 disabled:opacity-50"
                  >
                    {scanning ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" /> Scanning & Parsing Invoice...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-lime-300" /> Extract Invoice Data Now
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              /* Review & Edit Extracted Data */
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-emerald-50 to-lime-50 border border-emerald-200 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xs shadow-md">
                      🤖 AI
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-emerald-950 font-poppins">CrewAI Multi-Agent Extraction Complete</span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-800 text-[10px] font-semibold uppercase tracking-wider">Verified Agentic</span>
                      </div>
                      <p className="text-xs text-emerald-800 mt-0.5">
                        <strong className="font-semibold text-emerald-900">Agents Used:</strong> Invoice Reader Agent + Accounting Auditor Agent | Review extracted fields below or press <kbd className="px-1 py-0.5 bg-white border border-emerald-300 rounded text-[11px] font-mono font-bold text-slate-700">Enter ↵</kbd> to confirm.
                      </p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setExtracted(null)} className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 underline shrink-0">
                    📸 Scan Another Bill
                  </button>
                </div>


                {/* Supplier & Invoice Fields */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                  <div>
                    <label className="agri-label">Vendor / Seller Name</label>
                    <input
                      className="agri-input text-sm"
                      value={extracted.supplier_name || ""}
                      onChange={(e) => updateExtractedField("supplier_name", e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="agri-label">Invoice Number</label>
                    <input
                      className="agri-input text-sm font-mono"
                      value={extracted.invoice_number || ""}
                      onChange={(e) => updateExtractedField("invoice_number", e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="agri-label">Invoice Date</label>
                    <input
                      type="date"
                      className="agri-input text-sm"
                      value={extracted.invoice_date || todayISO()}
                      onChange={(e) => updateExtractedField("invoice_date", e.target.value)}
                    />
                  </div>
                </div>

                {/* Extracted Line Items Table */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-poppins font-semibold text-slate-800 text-sm">Extracted Line Items ({extracted.items?.length || 0})</h3>
                    <button type="button" onClick={addItem} className="text-xs text-agri-primary font-semibold flex items-center gap-1 hover:underline">
                      <Plus className="w-3.5 h-3.5" /> Add Line Item
                    </button>
                  </div>

                  <div className="overflow-x-auto border border-slate-200 rounded-2xl">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-100 border-b border-slate-200">
                        <tr>
                          <th className="agri-th">#</th>
                          <th className="agri-th">Item Description</th>
                          <th className="agri-th">Batch</th>
                          <th className="agri-th">Expiry</th>
                          <th className="agri-th">Unit</th>
                          <th className="agri-th">Qty</th>
                          <th className="agri-th">Unit Price (₹)</th>
                          <th className="agri-th">Total Amount (₹)</th>
                          <th className="agri-th"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {extracted.items?.map((it, i) => (
                          <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50">
                            <td className="agri-td text-slate-400">{i + 1}</td>
                            <td className="agri-td">
                              <input
                                className="w-full border border-slate-200 rounded px-2 py-1 focus:ring-1 focus:ring-emerald-500"
                                value={it.product_name || ""}
                                onChange={(e) => updateItemField(i, "product_name", e.target.value)}
                              />
                            </td>
                            <td className="agri-td">
                              <input
                                className="w-24 border border-slate-200 rounded px-2 py-1 font-mono"
                                value={it.batch_number || ""}
                                onChange={(e) => updateItemField(i, "batch_number", e.target.value)}
                              />
                            </td>
                            <td className="agri-td">
                              <input
                                type="date"
                                className="w-28 border border-slate-200 rounded px-2 py-1"
                                value={it.expiry_date || ""}
                                onChange={(e) => updateItemField(i, "expiry_date", e.target.value)}
                              />
                            </td>
                            <td className="agri-td">
                              <input
                                className="w-16 border border-slate-200 rounded px-2 py-1"
                                value={it.unit || "Unit"}
                                onChange={(e) => updateItemField(i, "unit", e.target.value)}
                              />
                            </td>
                            <td className="agri-td">
                              <input
                                type="number"
                                min="0"
                                step="any"
                                className="w-20 border border-slate-200 rounded px-2 py-1 font-semibold"
                                value={it.qty}
                                onChange={(e) => updateItemField(i, "qty", Number(e.target.value))}
                              />
                            </td>
                            <td className="agri-td">
                              <input
                                type="number"
                                min="0"
                                step="any"
                                className="w-24 border border-slate-200 rounded px-2 py-1 font-semibold text-right"
                                value={it.unit_price}
                                onChange={(e) => updateItemField(i, "unit_price", Number(e.target.value))}
                              />
                            </td>
                            <td className="agri-td font-semibold text-slate-800 text-right">
                              {fmtCurrency(it.amount || (it.qty * it.unit_price))}
                            </td>
                            <td className="agri-td">
                              <button type="button" onClick={() => removeItem(i)} className="text-slate-400 hover:text-red-500 p-1">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Subtotal, Tax, Total Amounts */}
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 grid grid-cols-1 md:grid-cols-4 gap-4 items-center text-xs">
                  <div>
                    <label className="agri-label">Subtotal Amount</label>
                    <div className="font-semibold text-slate-800 text-sm">{fmtCurrency(extracted.subtotal || 0)}</div>
                  </div>
                  <div>
                    <label className="agri-label">CGST Amount (₹)</label>
                    <input
                      type="number"
                      step="any"
                      className="agri-input text-xs"
                      value={extracted.cgst || 0}
                      onChange={(e) => updateExtractedField("cgst", Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="agri-label">SGST Amount (₹)</label>
                    <input
                      type="number"
                      step="any"
                      className="agri-input text-xs"
                      value={extracted.sgst || 0}
                      onChange={(e) => updateExtractedField("sgst", Number(e.target.value))}
                    />
                  </div>
                  <div className="text-right flex flex-col items-end justify-center">
                    <span className="text-xs text-slate-500">Total Amount</span>
                    <div className="font-poppins font-bold text-xl text-agri-primary">{fmtCurrency(extracted.total || 0)}</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    💡 Tip: Press <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded font-mono font-bold">Enter</kbd> to save directly into database.
                  </span>
                  <div className="flex items-center gap-3">
                    <button type="button" onClick={onClose} className="agri-btn-secondary py-2.5 px-4 text-xs">
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSavePurchase}
                      disabled={saving}
                      className="agri-btn-primary py-2.5 px-6 text-xs disabled:opacity-50"
                      data-testid="btn-confirm-scanned-purchase"
                    >
                      {saving ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Saving Purchase...
                        </>
                      ) : (
                        <>
                          <Check className="w-4 h-4" /> Confirm & Add to Purchase List
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

