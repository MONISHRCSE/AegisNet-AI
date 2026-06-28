import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { useWebSocket } from '@/websocket/useWebSocket'
import AppLayout from '@/layouts/AppLayout'
import LoadingScreen from '@/components/ui/LoadingScreen'

const Login     = lazy(() => import('@/pages/Login'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Topology  = lazy(() => import('@/pages/Topology'))
const Threats   = lazy(() => import('@/pages/Threats'))
const Honeypots = lazy(() => import('@/pages/Honeypots'))
const Decoys    = lazy(() => import('@/pages/Decoys'))
const Forensics = lazy(() => import('@/pages/Forensics'))

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function ProtectedRoutes() {
  useWebSocket()
  return (
    <AppLayout>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route index         element={<Dashboard />} />
          <Route path="topology"  element={<Topology />} />
          <Route path="threats"   element={<Threats />} />
          <Route path="honeypots" element={<Honeypots />} />
          <Route path="decoys"    element={<Decoys />} />
          <Route path="forensics" element={<Forensics />} />
        </Routes>
      </Suspense>
    </AppLayout>
  )
}

export default function App() {
  const { token } = useAuthStore()
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Suspense fallback={<LoadingScreen />}>
          <Routes>
            <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
            <Route path="/*"     element={token ? <ProtectedRoutes /> : <Navigate to="/login" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
