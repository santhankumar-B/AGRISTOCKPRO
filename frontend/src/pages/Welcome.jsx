import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sprout, ArrowRight, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { toast } from "sonner";

export default function Welcome() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  if (!user) return <Navigate to="/login" replace />;
  if (user.name && user.name.trim()) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return toast.error("Please enter your name");
    setSaving(true);
    try {
      await api.put("/auth/profile", { name: name.trim() });
      await refresh();
      toast.success(`Welcome aboard, ${name.trim()}!`);
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Something went wrong");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-agri-bg flex items-center justify-center p-6 relative overflow-hidden">
      {/* Decorative background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-emerald-100/60 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 w-[500px] h-[500px] rounded-full bg-lime-100/60 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-lg bg-white/90 backdrop-blur-xl border border-white/60 rounded-3xl shadow-2xl p-10"
        data-testid="welcome-card"
      >
        <div className="flex flex-col items-center text-center">
          <motion.div
            initial={{ scale: 0.6, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
            className="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#15803D] to-[#65A30D] flex items-center justify-center shadow-button mb-5"
          >
            <Sprout className="w-10 h-10 text-white" strokeWidth={2.2} />
          </motion.div>
          <h1 className="font-poppins font-bold text-3xl text-slate-900">Welcome to AgriStock Pro!</h1>
          <p className="text-slate-500 mt-2 max-w-sm">
            Before we get you set up, tell us your name so we can personalize your workspace.
          </p>
          <div className="text-xs text-slate-400 mt-3 font-mono">
            Signed in as <span className="text-slate-600 font-semibold">@{user.username}</span>
          </div>
        </div>

        <form onSubmit={submit} className="mt-8 space-y-5">
          <div>
            <label className="agri-label">Your Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                autoFocus
                data-testid="welcome-name-input"
                className="agri-input pl-10 text-base py-3"
                placeholder="e.g. Ramesh Patil"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={80}
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">This is how you'll appear across the app.</p>
          </div>

          <motion.button
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={saving || !name.trim()}
            data-testid="welcome-continue"
            className="agri-btn-primary w-full py-3 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {saving ? "Setting up..." : (<>Continue to Dashboard <ArrowRight className="w-4 h-4" /></>)}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}
