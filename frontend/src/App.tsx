import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "./components/layout/AppShell";
import { Campaigns } from "./pages/Campaigns";
import { Analytics } from "./pages/Analytics";
import { Comparisons } from "./pages/Comparisons";
import { AlertsActions } from "./pages/AlertsActions";
import { AuditLog } from "./pages/AuditLog";
import { Settings } from "./pages/Settings";
import { LiveMonitor } from "./pages/LiveMonitor";
import { Login } from "./pages/Login";
import { ProtectedRoute, PublicAuthRoute } from "./components/layout/ProtectedRoute";
import { CreateCampaignDialog } from "./components/common/CreateCampaignDialog";
import { useAuthStore } from "./store/authStore";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Route (Redirects to /campaigns if already logged in) */}
          <Route
            path="/login"
            element={
              <PublicAuthRoute>
                <Login />
              </PublicAuthRoute>
            }
          />

          {/* Protected Dashboard Routes (Redirects to /login if unauthenticated) */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<Navigate to="/campaigns" replace />} />
              <Route path="/campaigns" element={<Campaigns />} />
              <Route path="/campaigns/:campaignId" element={<LiveMonitor />} />
              <Route path="/live-monitor" element={<LiveMonitor />} />
              <Route path="/replay" element={<LiveMonitor />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/comparisons" element={<Comparisons />} />
              <Route path="/alerts" element={<AlertsActions />} />
              <Route path="/audit-log" element={<AuditLog />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/campaigns" replace />} />
            </Route>
          </Route>
        </Routes>
        <CreateCampaignDialog />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
