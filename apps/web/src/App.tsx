import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { DomainPage } from './pages/DomainPage';
import { CloudGpuPage } from './pages/CloudGpuPage';
import { UploadPage } from './pages/UploadPage';
import { phase4Routes } from './routes';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="cloud-gpu" element={<CloudGpuPage />} />
          {phase4Routes
            .filter((route) => route.path !== '/' && route.path !== '/upload')
            .map((route) => (
              <Route
                key={route.path}
                path={route.path.replace(/^\//, '')}
                element={<DomainPage title={route.page} />}
              />
            ))}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}