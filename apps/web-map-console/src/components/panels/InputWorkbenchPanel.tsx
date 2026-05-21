import { Play } from "lucide-react";
import { useState } from "react";
import { rallyApi } from "../../lib/api/rallyApi";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function InputWorkbenchPanel() {
  const rawText = useRallyWorkspaceStore((state) => state.rawText);
  const setRawText = useRallyWorkspaceStore((state) => state.setRawText);
  const applyParsedRally = useRallyWorkspaceStore((state) => state.applyParsedRally);
  const [status, setStatus] = useState("Ready");

  async function handleParse() {
    setStatus("Parsing");
    try {
      const result = await rallyApi.parse({ raw_text: rawText });
      applyParsedRally(result);
      setStatus(result.next_action || result.status);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Parse failed");
    }
  }

  return (
    <div className="panel-section">
      <h2 className="panel-heading">Soal Rally</h2>
      <textarea
        className="textarea"
        value={rawText}
        onChange={(event) => setRawText(event.target.value)}
        placeholder="Tempel soal rally, hasil OCR, atau instruksi sub-trayek di sini."
      />
      <div className="button-row">
        <button className="icon-button primary" type="button" onClick={handleParse}>
          <Play size={16} /> Parse
        </button>
      </div>
      <p className="metric-label">{status}</p>
    </div>
  );
}
