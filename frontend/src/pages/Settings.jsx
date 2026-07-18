import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api from "@/lib/api";
import { Save, Settings as SettingsIcon, Building2, Receipt, Package } from "lucide-react";
import { toast } from "sonner";

export default function Settings() {
  const [form, setForm] = useState(null);
  const [tab, setTab] = useState("company");

  useEffect(() => { api.get("/settings").then((r) => setForm(r.data)); }, []);

  const save = async () => {
    await api.put("/settings", form);
    toast.success("Settings saved");
  };

  if (!form) return (<><Navbar title="Settings" subtitle="Loading..." /><div className="p-8" /></>);

  const set = (k, v) => setForm({ ...form, [k]: v });

  const tabs = [
    { k: "company", label: "Company", icon: Building2 },
    { k: "invoice", label: "Invoice", icon: Receipt },
    { k: "inventory", label: "Inventory", icon: Package },
    { k: "business", label: "Business", icon: SettingsIcon },
  ];

  return (
    <>
      <Navbar title="Settings" subtitle="Configure your business & preferences." />
      <div className="p-8">
        <div className="agri-card p-8">
          <div className="flex gap-2 border-b border-slate-100 mb-8 -mx-2">
            {tabs.map((t) => {
              const Icon = t.icon;
              return (
                <button key={t.k} onClick={() => setTab(t.k)} data-testid={`settings-tab-${t.k}`}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${tab === t.k ? "border-agri-primary text-agri-primary" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
                  <Icon className="w-4 h-4" /> {t.label}
                </button>
              );
            })}
          </div>

          {tab === "company" && (
            <div className="grid grid-cols-2 gap-6">
              <div><label className="agri-label">Company Name</label><input className="agri-input" value={form.company_name} onChange={(e) => set("company_name", e.target.value)} data-testid="setting-company-name" /></div>
              <div><label className="agri-label">Email</label><input className="agri-input" value={form.company_email} onChange={(e) => set("company_email", e.target.value)} /></div>
              <div><label className="agri-label">Phone</label><input className="agri-input" value={form.company_phone} onChange={(e) => set("company_phone", e.target.value)} /></div>
              <div><label className="agri-label">GST Number</label><input className="agri-input" value={form.gst_number} onChange={(e) => set("gst_number", e.target.value)} /></div>
              <div className="col-span-2"><label className="agri-label">Address</label><textarea rows={3} className="agri-input" value={form.company_address} onChange={(e) => set("company_address", e.target.value)} /></div>
              <div className="col-span-2"><label className="agri-label">Logo URL</label><input className="agri-input" value={form.logo_url} onChange={(e) => set("logo_url", e.target.value)} /></div>
            </div>
          )}

          {tab === "invoice" && (
            <div className="grid grid-cols-2 gap-6">
              <div><label className="agri-label">Sales Invoice Prefix</label><input className="agri-input" value={form.invoice_prefix_sale} onChange={(e) => set("invoice_prefix_sale", e.target.value)} /></div>
              <div><label className="agri-label">Purchase Invoice Prefix</label><input className="agri-input" value={form.invoice_prefix_purchase} onChange={(e) => set("invoice_prefix_purchase", e.target.value)} /></div>
              <div><label className="agri-label">Default Tax Rate (%)</label><input type="number" className="agri-input" value={form.tax_rate} onChange={(e) => set("tax_rate", Number(e.target.value))} /></div>
            </div>
          )}

          {tab === "inventory" && (
            <div className="grid grid-cols-2 gap-6">
              <div className="flex items-center gap-3"><input type="checkbox" checked={form.low_stock_alert} onChange={(e) => set("low_stock_alert", e.target.checked)} id="lowstock" /><label htmlFor="lowstock" className="text-sm text-slate-700">Enable low stock alerts</label></div>
              <div><label className="agri-label">Expiry Alert (days before)</label><input type="number" className="agri-input" value={form.expiry_alert_days} onChange={(e) => set("expiry_alert_days", Number(e.target.value))} /></div>
            </div>
          )}

          {tab === "business" && (
            <div className="grid grid-cols-2 gap-6">
              <div><label className="agri-label">Currency</label><select className="agri-input" value={form.currency} onChange={(e) => set("currency", e.target.value)}>{["INR", "USD", "EUR", "GBP"].map((o) => <option key={o}>{o}</option>)}</select></div>
              <div><label className="agri-label">Currency Symbol</label><input className="agri-input" value={form.currency_symbol} onChange={(e) => set("currency_symbol", e.target.value)} /></div>
              <div><label className="agri-label">Timezone</label><select className="agri-input" value={form.timezone} onChange={(e) => set("timezone", e.target.value)}>{["Asia/Kolkata", "UTC", "America/New_York", "Europe/London"].map((o) => <option key={o}>{o}</option>)}</select></div>
              <div><label className="agri-label">Language</label><select className="agri-input" value={form.language} onChange={(e) => set("language", e.target.value)}>{["English", "Hindi", "Marathi", "Telugu"].map((o) => <option key={o}>{o}</option>)}</select></div>
            </div>
          )}

          <div className="flex justify-end mt-8"><button className="agri-btn-primary" onClick={save} data-testid="btn-save-settings"><Save className="w-4 h-4" /> Save Settings</button></div>
        </div>
      </div>
    </>
  );
}
