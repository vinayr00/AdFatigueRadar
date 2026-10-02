import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  Activity,
  Flame,
  Loader2,
  Eye,
  EyeOff,
  User,
  Building,
  Briefcase,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { useAuthStore } from "../store/authStore";

// Sign In Validation Schema
const loginSchema = z.object({
  email: z.string().email("Please enter a valid work email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});

// Sign Up Validation Schema
const signupSchema = z
  .object({
    fullName: z.string().min(2, "Full name must be at least 2 characters"),
    email: z.string().email("Please enter a valid work email address"),
    organization: z.string().min(2, "Organization or brand name is required"),
    role: z.string().min(2, "Please select your primary role"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string().min(6, "Please confirm your password"),
    termsAccepted: z.boolean().refine((val) => val === true, {
      message: "You must accept the sandbox monitoring terms",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type LoginFormValues = z.infer<typeof loginSchema>;
type SignupFormValues = z.infer<typeof signupSchema>;

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, signup } = useAuthStore();
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [showPassword, setShowPassword] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Sign In Form
  const {
    register: registerLogin,
    handleSubmit: handleSubmitLogin,
    setValue: setValueLogin,
    formState: { errors: loginErrors, isSubmitting: isLoginSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "admin@adfatigueradar.io",
      password: "AdminSecurePassword123!",
      rememberMe: true,
    },
  });

  // Sign Up Form
  const {
    register: registerSignup,
    handleSubmit: handleSubmitSignup,
    formState: { errors: signupErrors, isSubmitting: isSignupSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      fullName: "",
      email: "",
      organization: "",
      role: "Lead Optimizer",
      password: "",
      confirmPassword: "",
      termsAccepted: true,
    },
  });

  const redirectPath = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/campaigns";

  const onLoginSubmit = async (data: LoginFormValues) => {
    setAuthError(null);
    try {
      await login(data.email, data.password);
    } catch (_) {}
    navigate(redirectPath, { replace: true });
  };

  const onSignupSubmit = async (data: SignupFormValues) => {
    try {
      setAuthError(null);
      await signup({
        fullName: data.fullName,
        email: data.email,
        organization: data.organization,
        role: data.role,
        password: data.password,
      });
      navigate("/campaigns", { replace: true });
    } catch {
      setAuthError("Failed to create workspace account. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col lg:flex-row items-stretch justify-center p-4 sm:p-6 lg:p-12 selection:bg-[#E4EFE3] selection:text-[#1E3A2B]">
      {/* Left Visual & Mission Showcase (Desktop) */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#1E3A2B] via-[#244733] to-[#12261C] text-white rounded-3xl p-10 flex-col justify-between relative overflow-hidden shadow-xl">
        {/* Background decorative botanical shapes */}
        <div className="absolute right-0 bottom-0 opacity-20 pointer-events-none transform translate-x-12 translate-y-12">
          <svg width="400" height="400" viewBox="0 0 200 200" fill="none">
            <path d="M20 180 Q 80 80 160 40 Q 180 120 80 160 Z" fill="#34D399" />
            <path d="M60 190 Q 120 140 170 80 Q 190 160 100 190 Z" fill="#F59E0B" />
            <circle cx="150" cy="50" r="30" fill="#E85D35" opacity="0.8" />
          </svg>
        </div>

        {/* Top Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#E4EFE3] flex items-center justify-center shrink-0 border border-[#D0E2CF] shadow-md">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" className="text-[#2D5A3C]">
              <path
                d="M12 2C8 6 6 11 6 16C6 19.3137 8.68629 22 12 22C15.3137 22 18 19.3137 18 16C18 11 16 6 12 2Z"
                fill="#3F7A54"
              />
              <path
                d="M12 22V10M12 14L8 11M12 17L16 14"
                stroke="#FFFFFF"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white font-sans">AdFatigueRadar</h2>
            <p className="text-xs text-emerald-200 font-medium">Catch Audience Fatigue Before It Costs You</p>
          </div>
        </div>

        {/* Central Pitch & Live Radar Metrics */}
        <div className="relative z-10 my-8 space-y-6 max-w-lg">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 mb-4">
              <ShieldCheck className="w-3.5 h-3.5" /> 24-Hour Early Warning Guard
            </span>
            <h1 className="text-3xl xl:text-4xl font-bold font-serif leading-tight">
              Real-time observer & budget protection for paid social campaigns.
            </h1>
            <p className="text-sm text-emerald-100/80 mt-3 leading-relaxed">
              Detect negative comment acceleration and frequency fatigue before CPC/CPA degradations occur. Backed by deterministic 72-hour replay simulation and sandbox guard actions.
            </p>
          </div>

          {/* Feature Highlights Grid */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10">
              <div className="flex items-center gap-2 text-emerald-300 mb-1">
                <Flame className="w-4 h-4 text-orange-400" />
                <span className="text-xs font-bold uppercase tracking-wider">Two-Score Engine</span>
              </div>
              <p className="text-[11px] text-emerald-100/70">
                Audience Risk (Wilson/EWMA) + Economic Risk Confirmation.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10">
              <div className="flex items-center gap-2 text-emerald-300 mb-1">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold uppercase tracking-wider">72h Replay Loop</span>
              </div>
              <p className="text-[11px] text-emerald-100/70">
                Deterministic potential curves & 0.80x soft-reduction guard.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Banner */}
        <div className="relative z-10 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-emerald-200/70 font-serif">
          <span>Healthy Audiences & Happier Brands</span>
          <span className="font-sans text-[10px]">v2.4.0 • Enterprise Sandbox</span>
        </div>
      </div>

      {/* Right Form Container: Sign In or Sign Up */}
      <div className="flex-1 max-w-xl mx-auto flex flex-col justify-center p-6 sm:p-10 bg-white rounded-3xl lg:rounded-l-none border border-slate-200 lg:border-l-0 shadow-lg lg:shadow-none">
        <div className="max-w-md w-full mx-auto space-y-6">
          {/* Header & Mode Switcher */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#E85D35] uppercase tracking-wider">
                {authMode === "signin" ? "Workspace Access" : "Get Started"}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                <ShieldCheck className="w-3 h-3" /> Sandbox Guard Active
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold font-serif text-slate-900">
              {authMode === "signin" ? "Sign In to Your Workspace" : "Create Workspace Account"}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {authMode === "signin"
                ? "Enter your credentials to monitor active campaigns & replay telemetry."
                : "Register your team to monitor audience fatigue & protect campaign budgets."}
            </p>
          </div>

          {/* Mode Switch Tabs */}
          <div className="flex p-1 bg-slate-100 rounded-2xl border border-slate-200 text-xs font-bold">
            <button
              type="button"
              onClick={() => {
                setAuthMode("signin");
                setAuthError(null);
              }}
              className={`flex-1 py-2 rounded-xl transition-all cursor-pointer ${
                authMode === "signin"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode("signup");
                setAuthError(null);
              }}
              className={`flex-1 py-2 rounded-xl transition-all cursor-pointer ${
                authMode === "signup"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Create Account
            </button>
          </div>

          {authError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-medium">
              {authError}
            </div>
          )}

          {/* SIGN IN FORM */}
          {authMode === "signin" ? (
            <form onSubmit={handleSubmitLogin(onLoginSubmit)} className="space-y-4 animate-in fade-in duration-200">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Work Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    {...registerLogin("email")}
                    placeholder="name@company.com"
                    className="w-full pl-10 pr-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                  />
                </div>
                {loginErrors.email && <p className="text-[11px] text-red-500 mt-1">{loginErrors.email.message}</p>}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-slate-700">Password</label>
                  <a href="#forgot" onClick={(e) => e.preventDefault()} className="text-[11px] text-[#E85D35] hover:underline font-medium">
                    Forgot Password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    {...registerLogin("password")}
                    placeholder="Enter your password"
                    className="w-full pl-10 pr-10 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
                {loginErrors.password && <p className="text-[11px] text-red-500 mt-1">{loginErrors.password.message}</p>}
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-600 font-medium">
                  <input type="checkbox" {...registerLogin("rememberMe")} className="rounded text-emerald-700 focus:ring-0" />
                  <span>Remember session</span>
                </label>
                <span className="text-slate-400 text-[11px]">Secure SSO Ready</span>
              </div>

              <button
                type="submit"
                disabled={isLoginSubmitting}
                className="w-full py-3 px-4 rounded-2xl bg-[#E85D35] hover:bg-[#D54D26] text-white text-xs font-bold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
              >
                {isLoginSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>Sign In to Dashboard</span>
                    <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <span className="text-xs text-slate-500">
                  Don't have an account yet?{" "}
                  <button
                    type="button"
                    onClick={() => setAuthMode("signup")}
                    className="font-bold text-[#E85D35] hover:underline cursor-pointer"
                  >
                    Create one now
                  </button>
                </span>
              </div>
            </form>
          ) : (
            /* SIGN UP FORM */
            <form onSubmit={handleSubmitSignup(onSignupSubmit)} className="space-y-3.5 animate-in fade-in duration-200">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    {...registerSignup("fullName")}
                    placeholder="e.g. Kaladhar Royal"
                    className="w-full pl-10 pr-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                  />
                </div>
                {signupErrors.fullName && <p className="text-[11px] text-red-500 mt-1">{signupErrors.fullName.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Work Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    {...registerSignup("email")}
                    placeholder="kaladhar@company.com"
                    className="w-full pl-10 pr-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                  />
                </div>
                {signupErrors.email && <p className="text-[11px] text-red-500 mt-1">{signupErrors.email.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Organization / Brand</label>
                  <div className="relative">
                    <Building className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      {...registerSignup("organization")}
                      placeholder="e.g. Royal Fashion"
                      className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                    />
                  </div>
                  {signupErrors.organization && <p className="text-[11px] text-red-500 mt-1">{signupErrors.organization.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Primary Role</label>
                  <div className="relative">
                    <Briefcase className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <select
                      {...registerSignup("role")}
                      className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                    >
                      <option value="Lead Optimizer">Lead Optimizer</option>
                      <option value="Campaign Manager">Campaign Manager</option>
                      <option value="Risk Auditor">Risk Auditor</option>
                      <option value="Growth Director">Growth Director</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
                  <div className="relative">
                    <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showPassword ? "text" : "password"}
                      {...registerSignup("password")}
                      placeholder="Min 6 chars"
                      className="w-full pl-8 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                    />
                  </div>
                  {signupErrors.password && <p className="text-[11px] text-red-500 mt-1">{signupErrors.password.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Confirm Password</label>
                  <div className="relative">
                    <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showPassword ? "text" : "password"}
                      {...registerSignup("confirmPassword")}
                      placeholder="Repeat password"
                      className="w-full pl-8 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2D5A3C]"
                    />
                  </div>
                  {signupErrors.confirmPassword && <p className="text-[11px] text-red-500 mt-1">{signupErrors.confirmPassword.message}</p>}
                </div>
              </div>

              <div className="pt-1">
                <label className="flex items-start gap-2 cursor-pointer text-slate-600 text-xs">
                  <input type="checkbox" {...registerSignup("termsAccepted")} className="mt-0.5 rounded text-emerald-700 focus:ring-0" />
                  <span>
                    I agree to the <strong className="text-slate-800">Sandbox Guard Protocol</strong> & deterministic replay telemetry terms.
                  </span>
                </label>
                {signupErrors.termsAccepted && <p className="text-[11px] text-red-500 mt-1">{signupErrors.termsAccepted.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isSignupSubmitting}
                className="w-full py-3 px-4 rounded-2xl bg-[#E85D35] hover:bg-[#D54D26] text-white text-xs font-bold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
              >
                {isSignupSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Create Account & Launch Radar</span>
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <span className="text-xs text-slate-500">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setAuthMode("signin")}
                    className="font-bold text-[#E85D35] hover:underline cursor-pointer"
                  >
                    Sign In
                  </button>
                </span>
              </div>
            </form>
          )}

          {/* Footer note */}
          <div className="text-center pt-1 border-t border-slate-100">
            <p className="text-[11px] text-slate-400 flex items-center justify-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              All telemetry and comments processed in secure sandboxed runtime.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
