import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { MainLayout } from './layouts/MainLayout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { PageLoader } from './components/Loader';

// Lazy load pages
const Login = React.lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Monitoring = React.lazy(() => import('./pages/Monitoring').then(m => ({ default: m.Monitoring })));
const ProcessMonitor = React.lazy(() => import('./pages/ProcessMonitor').then(m => ({ default: m.ProcessMonitor })));
const ThreatDetection = React.lazy(() => import('./pages/ThreatDetection').then(m => ({ default: m.ThreatDetection })));
const ThreatHistory = React.lazy(() => import('./pages/ThreatHistory').then(m => ({ default: m.ThreatHistory })));
const Analytics = React.lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
const Reports = React.lazy(() => import('./pages/Reports').then(m => ({ default: m.Reports })));
const Settings = React.lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppProvider>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public Authentication Route */}
              <Route path="/login" element={<Login />} />

              {/* Protected Dashboard & App Routes */}
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<PageLoader />}>
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/monitoring" element={<Monitoring />} />
                          <Route path="/process-monitor" element={<ProcessMonitor />} />
                          <Route path="/threat-detection" element={<ThreatDetection />} />
                          <Route path="/threat-history" element={<ThreatHistory />} />
                          <Route path="/analytics" element={<Analytics />} />
                          <Route path="/reports" element={<Reports />} />
                          <Route path="/settings" element={<Settings />} />
                          <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Suspense>

          <Toaster
            position="bottom-right"
            gutter={8}
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1E293B',
                color: '#F1F5F9',
                border: '1px solid #334155',
                borderRadius: '12px',
                fontSize: '13px',
                fontFamily: '"Inter", system-ui, sans-serif',
                padding: '12px 16px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
              },
              success: {
                iconTheme: {
                  primary: '#10B981',
                  secondary: '#F1F5F9',
                },
              },
              error: {
                iconTheme: {
                  primary: '#EF4444',
                  secondary: '#F1F5F9',
                },
              },
            }}
          />
        </AppProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
