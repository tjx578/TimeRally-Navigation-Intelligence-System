import { Check, Flag, MapPinned, Navigation, TriangleAlert } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

function formatDistance(distanceKm: number | null) {
  return distanceKm === null ? "perlu OCR" : `${distanceKm.toFixed(2)} km`;
}

function modeLabel(mode: string) {
  if (mode === "fixed_second") return "Tetap detik";
  if (mode === "fixed_minute") return "Tetap menit";
  if (mode === "average_speed") return "Rata-rata";
  if (mode === "remaining_distance") return "Sisa finish";
  if (mode === "free_time") return "Santai";
  return "Zero trip";
}

function endpointStatusLabel(status: string) {
  if (status === "explicit") return "explicit";
  if (status === "inherited") return "inherited";
  if (status === "missing_location") return "perlu lokasi";
  if (status === "inferred_last_waypoint") return "infer last";
  return "missing";
}

export function SubTrayekMapPanel() {
  const routes = useRallyWorkspaceStore((state) => state.mappedSubTrayeks);
  const execution = useRallyWorkspaceStore((state) => state.execution);
  const selectSubTrayekRoute = useRallyWorkspaceStore((state) => state.selectSubTrayekRoute);
  const updateSubTrayekEndpoint = useRallyWorkspaceStore((state) => state.updateSubTrayekEndpoint);
  const finishActiveSubTrayek = useRallyWorkspaceStore((state) => state.finishActiveSubTrayek);
  const activeRoute = routes.find((route) => route.id === execution.activeSubTrayekId) ?? routes[0];
  const endpointBlocked = activeRoute?.needsUserStart || activeRoute?.needsUserFinish;

  if (!activeRoute) {
    return (
      <div className="panel-section">
        <h2 className="panel-heading">Mapping Sub-Trayek</h2>
        <p className="metric-label">Belum ada sub-trayek yang bisa ditampilkan di peta.</p>
      </div>
    );
  }

  return (
    <div className="panel-section">
      <div className="panel-title-row">
        <h2 className="panel-heading">Mapping Sub-Trayek</h2>
        <span className="status-pill">{routes.filter((route) => route.roadbookReady).length}/{routes.length}</span>
      </div>

      <div className="subtrayek-tabs" role="tablist" aria-label="Sub-trayek hasil mapping">
        {routes.map((route) => (
          <button
            className={`subtrayek-tab ${route.id === activeRoute.id ? "active" : ""} ${route.roadbookReady ? "done" : ""}`}
            key={route.id}
            type="button"
            onClick={() => selectSubTrayekRoute(route.id)}
          >
            {route.sub}
          </button>
        ))}
      </div>

      <div className="route-review">
        <div className="route-review-heading">
          <MapPinned size={16} />
          <div>
            <strong>Sub {activeRoute.sub}: {activeRoute.title}</strong>
            <span>{activeRoute.startLabel} - {activeRoute.finishLabel}</span>
          </div>
        </div>

        <div className="endpoint-editor-grid">
          <label className={activeRoute.needsUserStart ? "endpoint-field needs-review" : "endpoint-field"}>
            <span>
              Start
              <em>{endpointStatusLabel(activeRoute.startStatus)}</em>
            </span>
            <input
              aria-label={`Start Sub ${activeRoute.sub}`}
              value={activeRoute.startLabel}
              onChange={(event) => updateSubTrayekEndpoint(activeRoute.id, "start", event.target.value)}
            />
          </label>
          <label className={activeRoute.needsUserFinish ? "endpoint-field needs-review" : "endpoint-field"}>
            <span>
              Finish
              <em>{endpointStatusLabel(activeRoute.finishStatus)}</em>
            </span>
            <input
              aria-label={`Finish Sub ${activeRoute.sub}`}
              value={activeRoute.finishLabel}
              onChange={(event) => updateSubTrayekEndpoint(activeRoute.id, "finish", event.target.value)}
            />
          </label>
        </div>

        {endpointBlocked ? (
          <p className="metric-label endpoint-warning">
            <TriangleAlert size={13} /> Start/finish wajib lengkap sebelum routing final.
          </p>
        ) : null}

        <div className="route-review-grid">
          <span>Start {activeRoute.scheduledStartTime}</span>
          <span>Finish {activeRoute.scheduledFinishTime}</span>
          <span>{formatDistance(activeRoute.distanceKm)}</span>
          <span>{activeRoute.durationMinutes} menit</span>
          <span>{activeRoute.speedKmh ? `${activeRoute.speedKmh.toFixed(2)} km/jam` : "speed review"}</span>
          <span>{modeLabel(activeRoute.speedMode)}</span>
          <span>{activeRoute.kmPerSecond ? `${activeRoute.kmPerSecond.toFixed(6)} km/detik` : "tap review"}</span>
          <span>{activeRoute.waypointCount} waypoint</span>
        </div>

        <p className="metric-label">{activeRoute.routeSummary}</p>

        <div className="handoff-box">
          <span>
            <Navigation size={13} /> Driver: {execution.driverRunningSubTrayekId ? routes.find((route) => route.id === execution.driverRunningSubTrayekId)?.sub : "-"}
          </span>
          <span>Navi review: {execution.navigatorWorkingSubTrayekId ? routes.find((route) => route.id === execution.navigatorWorkingSubTrayekId)?.sub : "-"}</span>
        </div>

        <button
          className="icon-button primary full-width"
          type="button"
          onClick={finishActiveSubTrayek}
          disabled={endpointBlocked}
        >
          {activeRoute.roadbookReady ? <Check size={16} /> : <Flag size={16} />}
          {activeRoute.roadbookReady ? "Sudah Masuk Roadbook" : "Finish Sub Ini"}
        </button>
      </div>
    </div>
  );
}
