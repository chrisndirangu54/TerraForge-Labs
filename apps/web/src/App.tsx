import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { DomainPage } from './pages/DomainPage';
import { CloudGpuPage } from './pages/CloudGpuPage';
import { LoginPage } from './pages/LoginPage';
import { UploadPage } from './pages/UploadPage';
import { MapPage } from './pages/MapPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ReportsPage } from './pages/ReportsPage';
import { KrigingPage } from './pages/KrigingPage';
import { LabelingPage } from './pages/LabelingPage';
import { CopilotPage } from './pages/CopilotPage';
import { TargetingPage } from './pages/TargetingPage';
import { FinancialAnalysisPage } from './pages/FinancialAnalysisPage';
import { ModelTrainingPage } from './pages/ModelTrainingPage';
const DepositPage = lazy(() =>
  import('./pages/DepositPage').then((module) => ({ default: module.DepositPage })),
);
import { HydrogeologyPage } from './pages/HydrogeologyPage';
import { UrbanPage } from './pages/UrbanPage';
import { InfrastructurePage } from './pages/InfrastructurePage';
import { SatellitePage } from './pages/SatellitePage';
import { MarketplacePage } from './pages/MarketplacePage';
import { DigitalTwinPage } from './pages/DigitalTwinPage';
import { SettingsPage } from './pages/SettingsPage';
import { AdminPage } from './pages/AdminPage';
import { ARPage } from './pages/ARPage';
import { PlatformHubPage } from './pages/PlatformHubPage';
import { phase4Routes } from './routes';

const missionControlPages: Record<string, JSX.Element> = {
  '/map': <MapPage />,
  '/projects': <ProjectsPage />,
  '/reports': <ReportsPage />,
  '/kriging': <KrigingPage />,
  '/labeling': <LabelingPage />,
  '/copilot': <CopilotPage />,
  '/targeting': <TargetingPage />,
  '/financial': <FinancialAnalysisPage />,
  '/model-training': <ModelTrainingPage />,
  '/deposit': (
    <Suspense fallback={<p className="text-sediment-muted">Loading deposit viewer…</p>}>
      <DepositPage />
    </Suspense>
  ),
  '/hydrogeology': <HydrogeologyPage />,
  '/urban': <UrbanPage />,
  '/infrastructure': <InfrastructurePage />,
  '/satellite': <SatellitePage />,
  '/marketplace': <MarketplacePage />,
  '/digital-twin': <DigitalTwinPage />,
  '/settings': <SettingsPage />,
  '/admin': <AdminPage />,
  '/ar': <ARPage />,
  '/platform': <PlatformHubPage />,
};

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="login" element={<LoginPage />} />
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
                element={
                  missionControlPages[route.path] ?? <DomainPage title={route.page} />
                }
              />
            ))}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}