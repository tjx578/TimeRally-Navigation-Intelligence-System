import { Map, ShieldCheck } from "lucide-react";
import { InputWorkbenchPanel } from "../panels/InputWorkbenchPanel";
import { MasterClockPanel } from "../panels/MasterClockPanel";
import { ProbabilityRouteOptionsPanel } from "../panels/ProbabilityRouteOptionsPanel";
import { QuestionPhotoIntakePanel } from "../panels/QuestionPhotoIntakePanel";
import { RouteEditorPanel } from "../panels/RouteEditorPanel";
import { SubTrayekMapPanel } from "../panels/SubTrayekMapPanel";
import { SubTrayekValidationPanel } from "../panels/SubTrayekValidationPanel";
import { ValidationPanel } from "../panels/ValidationPanel";
import { WaypointInspectorPanel } from "../panels/WaypointInspectorPanel";
import { RallyMapCanvas } from "../map/RallyMapCanvas";
import { RouteEditorToolbar } from "../map/RouteEditorToolbar";
import { RoadbookTable } from "../tables/RoadbookTable";
import { TimingValidationTable } from "../tables/TimingValidationTable";

export function WorkspaceShell() {
  return (
    <div className="workspace">
      <header className="topbar">
        <Map size={18} />
        <div className="topbar-title">Time Rally Navigation Console</div>
        <div className="topbar-status">
          <ShieldCheck size={14} /> Championship workspace
        </div>
      </header>

      <main className="main-grid">
        <aside className="side-panel">
          <MasterClockPanel />
          <QuestionPhotoIntakePanel />
          <InputWorkbenchPanel />
          <RouteEditorPanel />
        </aside>

        <section className="map-region">
          <RallyMapCanvas />
          <RouteEditorToolbar />
        </section>

        <aside className="side-panel right">
          <ValidationPanel />
          <SubTrayekValidationPanel />
          <SubTrayekMapPanel />
          <ProbabilityRouteOptionsPanel />
          <WaypointInspectorPanel />
        </aside>
      </main>

      <section className="roadbook-region">
        <TimingValidationTable />
        <RoadbookTable />
      </section>
    </div>
  );
}
