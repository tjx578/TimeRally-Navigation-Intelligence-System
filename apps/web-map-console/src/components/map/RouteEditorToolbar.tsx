import { Eraser, GitBranch, Lock, Magnet, MousePointer2, Pencil, Scissors, Undo2 } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";
import type { RouteEditMode } from "../../types/rally";

const tools: Array<{ mode: RouteEditMode; label: string; icon: typeof MousePointer2 }> = [
  { mode: "inspect", label: "Inspect", icon: MousePointer2 },
  { mode: "draw", label: "Draw", icon: Pencil },
  { mode: "erase", label: "Erase", icon: Eraser },
  { mode: "repair", label: "Repair", icon: GitBranch },
  { mode: "split", label: "Split", icon: Scissors },
  { mode: "lock", label: "Lock", icon: Lock }
];

export function RouteEditorToolbar() {
  const editor = useRallyWorkspaceStore((state) => state.routeEditor);
  const setMode = useRallyWorkspaceStore((state) => state.setRouteEditMode);
  const toggleSnapToRoad = useRallyWorkspaceStore((state) => state.toggleSnapToRoad);

  return (
    <div className="route-toolbar" aria-label="Route editor tools">
      {tools.map((tool) => {
        const Icon = tool.icon;
        const active = editor.mode === tool.mode;
        return (
          <button
            className={`tool-button ${active ? "active" : ""}`}
            key={tool.mode}
            type="button"
            title={tool.label}
            onClick={() => setMode(tool.mode)}
          >
            <Icon size={16} />
          </button>
        );
      })}
      <div className="toolbar-divider" />
      <button
        className={`tool-button ${editor.snapToRoad ? "active" : ""}`}
        type="button"
        title={editor.snapToRoad ? "Snap to road active" : "Manual trace mode"}
        onClick={toggleSnapToRoad}
      >
        <Magnet size={16} />
      </button>
      <button className="tool-button" type="button" title="Undo last segment">
        <Undo2 size={16} />
      </button>
    </div>
  );
}

