import { motion } from "framer-motion";
import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { Eye, EyeOff, Lock, User, Shield, Sprout, LogIn } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

const leafPositions = Array.from({ length: 12 }, (_, i) => ({
  left: `${(i * 8.3) % 100}%`,
  duration: 10 + (i % 6) * 2,
  delay: (i * 0.7) % 8,
  size: 18 + (i % 4) * 6,
  rotate: (i * 45) % 360,
}));

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [showPass, setShowPass] = useState(false);
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.username, form.password);
      toast.success("Welcome back!");
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-agri-bg font-dmsans">
      {/* LEFT: Hero */}
      <div className="relative overflow-hidden hidden lg:block">
        <img
          src="https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1600&q=80"
          alt="Farm landscape"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-[#0F3D1F]/85 via-[#0F3D1F]/55 to-[#15803D]/30" />

        {/* Floating leaves */}
        {leafPositions.map((l, i) => (
          <motion.div
            key={i}
            className="absolute"
            style={{ left: l.left, top: "-5%" }}
            initial={{ y: -50, rotate: l.rotate, opacity: 0.55 }}
            animate={{ y: "110vh", rotate: l.rotate + 720, opacity: [0.55, 0.7, 0.4] }}
            transition={{ duration: l.duration, delay: l.delay, repeat: Infinity, ease: "linear" }}
          >
            <svg width={l.size} height={l.size} viewBox="0 0 24 24" fill="#A3E635" opacity="0.7">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
            </svg>
          </motion.div>
        ))}

        <div className="relative z-10 h-full flex flex-col p-14 text-white">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-14 h-14 rounded-2xl bg-white/15 backdrop-blur-md border border-white/25 flex items-center justify-center shadow-xl">
              <Sprout className="w-7 h-7 text-lime-300" strokeWidth={2.4} />
            </div>
            <div>
              <div className="font-poppins font-bold text-2xl">AgriStock Pro</div>
              <div className="text-xs text-white/70 tracking-widest uppercase">Agriculture Inventory ERP</div>
            </div>
          </motion.div>

          <div className="mt-auto max-w-lg">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="font-poppins font-bold text-4xl lg:text-5xl leading-tight"
            >
              Manage Your Agriculture Business Smarter
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="mt-4 text-white/80 text-lg"
            >
              Smart Inventory. Better Farming. Stronger Future.
            </motion.p>

            <motion.div
              initial="hidden"
              animate="show"
              variants={{ hidden: {}, show: { transition: { staggerChildren: 0.12, delayChildren: 0.5 } } }}
              className="grid grid-cols-3 gap-3 mt-10"
            >
              {[
                { title: "Inventory", desc: "Track batches & expiry", icon: "📦" },
                { title: "Reports", desc: "Sales & profit insights", icon: "📊" },
                { title: "Secure", desc: "Enterprise-grade auth", icon: "🛡" },
              ].map((c) => (
                <motion.div
                  key={c.title}
                  variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}
                  className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 text-white"
                >
                  <div className="text-2xl mb-1">{c.icon}</div>
                  <div className="font-semibold font-poppins">{c.title}</div>
                  <div className="text-xs text-white/70 mt-0.5">{c.desc}</div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </div>

      {/* RIGHT: Login card */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md bg-white/90 backdrop-blur-2xl border border-white/40 rounded-3xl shadow-2xl p-8 sm:p-10"
        >
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-green-50 border border-green-100 flex items-center justify-center mb-4">
              <Lock className="w-7 h-7 text-agri-primary" strokeWidth={2.2} />
            </div>
            <h2 className="font-poppins font-bold text-3xl text-slate-900">Welcome Back</h2>
            <p className="text-slate-500 mt-1 text-sm">Login to access your dashboard</p>
          </div>

          <form onSubmit={submit} className="space-y-5">
            <div>
              <label className="agri-label">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  data-testid="login-username"
                  className="agri-input pl-10"
                  placeholder="Enter your username"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="agri-label">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  data-testid="login-password"
                  type={showPass ? "text" : "password"}
                  className="agri-input pl-10 pr-10"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  data-testid="toggle-password"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer text-slate-600">
                <input type="checkbox" defaultChecked className="rounded border-slate-300 text-agri-primary focus:ring-agri-secondary" data-testid="remember-me" />
                Remember me
              </label>
              <a className="text-agri-primary font-medium hover:underline" href="#">Forgot Password?</a>
            </div>

            <button
              type="submit"
              disabled={loading}
              data-testid="login-submit"
              className="agri-btn-primary w-full py-3 disabled:opacity-70"
            >
              {loading ? "Signing in..." : (<><LogIn className="w-4 h-4" /> Login Securely</>)}
            </button>

            <div className="flex items-center gap-2 my-2 text-xs text-slate-400 uppercase tracking-wider">
              <div className="flex-1 h-px bg-slate-200" />
              <span>Secure Access</span>
              <div className="flex-1 h-px bg-slate-200" />
            </div>

            <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
              <Shield className="w-3.5 h-3.5 text-green-600" />
              Your data is 100% secure with us
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
