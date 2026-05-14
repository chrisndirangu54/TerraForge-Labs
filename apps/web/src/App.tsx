import { phase4Routes } from './routes';

export function App() {
  return (
    <main>
      <h1>TerraForge Phase 4 Platform</h1>
      <p>React + MapLibre + Cesium scaffold for geological, hydro, urban, infrastructure, and satellite workflows.</p>
      <ul>
        {phase4Routes.map((route) => (
          <li key={route.path}>{route.path} — {route.page}</li>
        ))}
      </ul>
    </main>
  );
}
