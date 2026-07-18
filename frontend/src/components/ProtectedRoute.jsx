import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-agri-bg">
        <div className="animate-pulse text-agri-primary font-poppins text-lg">Loading AgriStock Pro…</div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  // First-time onboarding: if the user has no name, force them to /welcome
  if ((!user.name || !user.name.trim()) && location.pathname !== "/welcome") {
    return <Navigate to="/welcome" replace />;
  }
  return children;
}
