import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency } from "@/lib/api";
import { motion } from "framer-motion";
import { FileSpreadsheet, Printer, TrendingUp, TrendingDown, DollarSign, Package } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, PieChart, Pie, Cell } from "recharts";

const COLORS = ["#15803D", "#65A30D", "#34D399", "#A3E635", "#064E3B", "#FDE047"];

export default function Reports() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/reports/summary").then((r) => setData(r.data)); }, []);
  if (!data) return (<><Navbar title="Reports" subtitle="Loading..." /><div className="p-8 text-slate-500">Loading reports...</div></>);

  const exportCSV = (rows, name) => {
    if (!rows.length) return;
    const headers = Object.keys(rows[0]);
    const csv = [headers.join(","), ...rows.map((r) => headers.map((h) => `"${(r[h] ?? "").toString().replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = `${name}.csv`; a.click();
  };

  const Stat = ({ icon: Icon, label, value, color }) => (
    <motion.div whileHover={{ y: -4 }} className="agri-card p-6">
      <div className={`w-11 h-11 rounded-xl ${color} flex items-center justify-center mb-4`}><Icon className="w-5 h-5 text-white" /></div>
      <div className="text-sm text-slate-500">{label}</div>
      <div className="font-poppins font-bold text-2xl text-slate-900 mt-1">{value}</div>
    </motion.div>
  );

  return (
    <>
      <Navbar title="Reports & Analytics" subtitle="Business intelligence for sales, purchase and profit." />
      <div className="p-8 space-y-6">
        <div className="flex justify-end gap-2">
          <button className="agri-btn-secondary" onClick={() => exportCSV(data.monthly, "monthly-report")} data-testid="btn-export-csv"><FileSpreadsheet className="w-4 h-4" /> Export Excel</button>
          <button className="agri-btn-secondary" onClick={() => window.print()}><Printer className="w-4 h-4" /> Print</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Stat icon={TrendingUp} label="Total Sales" value={fmtCurrency(data.total_sales)} color="bg-gradient-to-br from-[#15803D] to-[#65A30D]" />
          <Stat icon={TrendingDown} label="Total Purchases" value={fmtCurrency(data.total_purchases)} color="bg-gradient-to-br from-amber-500 to-amber-600" />
          <Stat icon={DollarSign} label="Total Profit" value={fmtCurrency(data.total_profit)} color="bg-gradient-to-br from-emerald-500 to-emerald-600" />
          <Stat icon={Package} label="Tax Collected" value={fmtCurrency(data.tax.cgst + data.tax.sgst)} color="bg-gradient-to-br from-blue-500 to-blue-600" />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="agri-card p-6 xl:col-span-2">
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Monthly Sales vs Purchases</h3>
            <div className="h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.monthly}>
                  <CartesianGrid vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip formatter={(v) => fmtCurrency(v)} />
                  <Legend />
                  <Bar dataKey="sales" fill="#15803D" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="purchases" fill="#65A30D" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="agri-card p-6">
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Inventory by Category</h3>
            {data.category_wise.length === 0 ? <div className="text-slate-400 text-sm py-8 text-center">No data</div> : (
              <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={data.category_wise} dataKey="stock_value" nameKey="category" innerRadius={50} outerRadius={100} paddingAngle={2}>
                      {data.category_wise.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v) => fmtCurrency(v)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="agri-card p-6">
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Top Customers</h3>
            {data.top_customers.length === 0 ? <div className="text-slate-400 text-sm py-8 text-center">No sales data</div> : (
              <div className="space-y-3">
                {data.top_customers.map((c, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-bold text-sm flex items-center justify-center">{i + 1}</div>
                      <div><div className="font-medium text-slate-800">{c.name}</div><div className="text-xs text-slate-500">{c.count} invoice{c.count !== 1 ? "s" : ""}</div></div>
                    </div>
                    <div className="font-semibold text-slate-800">{fmtCurrency(c.amount)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="agri-card p-6">
            <h3 className="font-poppins font-semibold text-lg text-slate-900 mb-4">Top Suppliers</h3>
            {data.top_suppliers.length === 0 ? <div className="text-slate-400 text-sm py-8 text-center">No purchase data</div> : (
              <div className="space-y-3">
                {data.top_suppliers.map((c, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-lime-50 text-lime-700 font-bold text-sm flex items-center justify-center">{i + 1}</div>
                      <div><div className="font-medium text-slate-800">{c.name}</div><div className="text-xs text-slate-500">{c.count} invoice{c.count !== 1 ? "s" : ""}</div></div>
                    </div>
                    <div className="font-semibold text-slate-800">{fmtCurrency(c.amount)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
