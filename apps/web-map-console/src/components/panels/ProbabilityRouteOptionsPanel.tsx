import { Check, GitCompare, X } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function ProbabilityRouteOptionsPanel() {
  const options = useRallyWorkspaceStore((state) => state.probabilityOptions);
  const selectedId = useRallyWorkspaceStore((state) => state.selectedProbabilityOptionId);
  const selectOption = useRallyWorkspaceStore((state) => state.selectProbabilityOption);
  const acceptOption = useRallyWorkspaceStore((state) => state.acceptProbabilityOption);
  const rejectOption = useRallyWorkspaceStore((state) => state.rejectProbabilityOption);

  return (
    <div className="panel-section probability-panel">
      <h2 className="panel-heading">Opsi Jalur Probabilitas</h2>
      {options.length === 0 ? (
        <p className="metric-label">Belum ada kandidat probabilitas.</p>
      ) : (
        options.map((option) => {
          const selected = selectedId === option.id;
          return (
            <article
              className={`candidate-card ${selected ? "selected" : ""}`}
              key={option.id}
              onClick={() => selectOption(option.id)}
            >
              <div className="candidate-header">
                <div>
                  <div className="candidate-title">{option.label}</div>
                  <div className="metric-label">
                    {option.missingWaypointLabel} - {option.provider}
                  </div>
                </div>
                <span className="confidence">{Math.round(option.confidence * 100)}%</span>
              </div>

              <div className="candidate-metrics">
                <span>Jarak {option.distanceDeviationPercent.toFixed(1)}%</span>
                <span>Waktu {option.timeDeviationSeconds}s</span>
                <span>Koridor {Math.round(option.routeCorridorFit * 100)}%</span>
              </div>

              <ul className="reason-list">
                {option.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>

              <div className="button-row compact">
                <button
                  className="icon-button primary"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    acceptOption(option.id);
                  }}
                >
                  <Check size={14} /> Pakai
                </button>
                <button
                  className="icon-button"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    rejectOption(option.id);
                  }}
                >
                  <X size={14} /> Tolak
                </button>
                <button className="icon-button" type="button">
                  <GitCompare size={14} /> Bandingkan
                </button>
              </div>
            </article>
          );
        })
      )}
    </div>
  );
}
