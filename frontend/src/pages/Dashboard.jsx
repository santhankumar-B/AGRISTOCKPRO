import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import api, { fmtCurrency, fmtDate } from "@/lib/api";
import { motion } from "framer-motion";
import { Package, ShoppingCart, Truck, AlertTriangle, TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Link } from "react-router-dom";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

const StatCard = ({ icon: Icon, iconBg, iconColor, label, value, trend, trendUp, testid }) => (
  <motion.div variants={fadeUp} whileHover={{ y: -4 }} className="agri-card p-6" data-testid={testid}>
    <div className="flex items-start justify-between">
      <div className={`w-12 h-12 rounded-2xl ${iconBg} flex items-center justify-center`}>
        <Icon className={`w-6 h-6 ${iconColor}`} strokeWidth={2} />
      </div>
    </div>
    <div className="mt-5">
      <div className="text-sm text-slate-500 font-medium">{label}</div>
      <div className="font-poppins font-bold text-3xl text-slate-900 mt-1">{value}</div>
      {trend && (
        <div className={`flex items-center gap-1 text-xs font-medium mt-2 ${trendUp ? "text-green-600" : "text-red-500"}`}>
          {trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {trend}
        </div>
      )}
    </div>
  </motion.div>
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/dashboard/stats").then((r) => setStats(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading || !stats) {
    return (
      <>
        <Navbar title="Welcome back!" subtitle="Loading your dashboard..." />
        <div className="p-8 grid grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="agri-card p-6 h-36 animate-pulse bg-slate-100" />
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar title={`Welcome back!`} subtitle="Here's what's happening with your business today." />
      <div className="p-8 space-y-6">
        {/* Stat Cards */}
        <motion.div initial="hidden" animate="show" variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
          <StatCard icon={Package} iconBg="bg-emerald-50" iconColor="text-emerald-600" label="Total Products" value={stats.total_products} trend="12.5% from last month" trendUp testid="stat-products" />
          <StatCard icon={ShoppingCart} iconBg="bg-lime-50" iconColor="text-lime-600" label="Today's Sales" value={fmtCurrency(stats.today_sales)} trend="18.6% from yesterday" trendUp testid="stat-sales" />
          <StatCard icon={Truck} iconBg="bg-amber-50" iconColor="text-amber-600" label="Today's Purchases" value={fmtCurrency(stats.today_purchases)} trend={`${stats.today_purchases > 0 ? "Great" : "Add first purchase"}`} trendUp testid="stat-purchases" />
          <StatCard icon={AlertTriangle} iconBg="bg-red-50" iconColor="text-red-500" label="Low Stock Items" value={stats.low_stock_count} trend={`${stats.expiring_count} expiring soon`} testid="stat-lowstock" />
        </motion.div>

        {/* Chart + Top Selling */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="agri-card p-6 xl:col-span-2" data-testid="chart-sales">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="font-poppins font-semibold text-lg text-slate-900">Sales Overview</h3>
                <div className="font-poppins font-bold text-2xl text-slate-900 mt-1">{fmtCurrency(stats.sales_trend.reduce((a, b) => a + b.total, 0))}</div>
                <div className="text-xs text-green-600 font-medium mt-0.5">Last 7 days</div>
              </div>
            </div>
            <div className="h-[260px] mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.sales_trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#15803D" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#15803D" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={(d) => new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `₹${v}`} />
                  <Tooltip formatter={(v) => fmtCurrency(v)} labelFormatter={(d) => fmtDate(d)} />
                  <Area type="monotone" dataKey="total" stroke="#15803D" strokeWidth={2.5} fill="url(#salesFill)" activeDot={{ r: 6 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="agri-card p-6" data-testid="top-selling">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-poppins font-semibold text-lg text-slate-900">Top Selling Products</h3>
              <Link to="/products" className="text-xs text-agri-primary font-medium hover:underline">View All</Link>
            </div>
            {stats.top_selling.length === 0 ? (
              <div className="text-sm text-slate-400 py-8 text-center">No sales yet. Create a sale to see top products.</div>
            ) : (
              <div className="space-y-3">
                {stats.top_selling.map((t, i) => (
                  <div key={t.product_id} className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 font-poppins font-bold text-sm flex items-center justify-center">{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-slate-800 truncate">{t.product_name}</div>
                      <div className="text-xs text-slate-500">{t.category || "Product"}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-slate-800">{t.qty} {t.unit || ""}</div>
                      <div className="text-xs text-slate-500">{fmtCurrency(t.amount)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* Recent Sales / Purchases / Low Stock */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <RecentList
            title="Recent Sales"
            testid="recent-sales"
            rows={stats.recent_sales}
            columns={[
              { key: "invoice_number", label: "Invoice", accent: true },
              { key: "customer_name", label: "Customer", fallback: "Walk-in" },
              { key: "total", label: "Amount", currency: true },
            ]}
            link="/sales"
            empty="No sales yet"
          />
          <RecentList
            title="Recent Purchases"
            testid="recent-purchases"
            rows={stats.recent_purchases}
            columns={[
              { key: "invoice_number", label: "Invoice", accent: true },
              { key: "supplier_name", label: "Supplier", fallback: "-" },
              { key: "total", label: "Amount", currency: true },
            ]}
            link="/purchase"
            empty="No purchases yet"
          />
          <div className="agri-card p-6" data-testid="low-stock-alerts">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-poppins font-semibold text-lg text-slate-900">Low Stock Alerts</h3>
              <Link to="/products?stock=low" className="text-xs text-agri-primary font-medium hover:underline">View All</Link>
            </div>
            {stats.low_stock_products.length === 0 ? (
              <div className="text-sm text-slate-400 py-8 text-center">All products are well-stocked ✓</div>
            ) : (
              <div className="space-y-3">
                {stats.low_stock_products.map((p) => (
                  <div key={p.id} className="flex items-center justify-between">
                    <div className="min-w-0">
                      <div className="font-medium text-sm text-slate-800 truncate">{p.name}</div>
                      <div className="text-xs text-slate-500">{p.category || "Product"}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-slate-800">Stock: {p.current_stock} {p.unit}</div>
                      <div className="text-xs text-red-500">Min: {p.minimum_stock} {p.unit}</div>
                    </div>
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

function RecentList({ title, rows, columns, link, empty, testid }) {
  return (
    <div className="agri-card p-6" data-testid={testid}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-poppins font-semibold text-lg text-slate-900">{title}</h3>
        <Link to={link} className="text-xs text-agri-primary font-medium hover:underline flex items-center gap-1">
          View All <ArrowUpRight className="w-3 h-3" />
        </Link>
      </div>
      {rows.length === 0 ? (
        <div className="text-sm text-slate-400 py-8 text-center">{empty}</div>
      ) : (
        <div className="space-y-3">
          {rows.map((r, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3 min-w-0">
                <div className={`font-medium ${columns[0].accent ? "text-agri-primary" : "text-slate-800"} truncate`}>{r[columns[0].key] || "-"}</div>
                <div className="text-slate-500 truncate hidden sm:block">{r[columns[1].key] || columns[1].fallback}</div>
              </div>
              <div className="font-semibold text-slate-800 whitespace-nowrap">
                {columns[2].currency ? fmtCurrency(r[columns[2].key]) : r[columns[2].key]}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
