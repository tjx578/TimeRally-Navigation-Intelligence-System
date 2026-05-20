import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function RoadbookTable() {
  const roadbook = useRallyWorkspaceStore((state) => state.roadbook);

  return (
    <section className="roadbook-table-region">
      <div className="roadbook-heading">
        <strong>Roadbook</strong>
        <span>{roadbook.length} sub siap</span>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>No</th>
            <th>Dari</th>
            <th>Ke</th>
            <th>Instruksi</th>
            <th>Jarak</th>
            <th>Kumulatif</th>
            <th>Durasi</th>
            <th>ETA</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {roadbook.length === 0 ? (
            <tr>
              <td colSpan={9}>Roadbook belum tersedia.</td>
            </tr>
          ) : (
            roadbook.map((leg, index) => (
              <tr key={leg.id}>
                <td>{index + 1}</td>
                <td>{leg.from}</td>
                <td>{leg.to}</td>
                <td>{leg.instruction}</td>
                <td>{leg.distanceKm.toFixed(2)} km</td>
                <td>{leg.cumulativeDistanceKm.toFixed(2)} km</td>
                <td>{Math.round(leg.durationSeconds / 60)} min</td>
                <td>{leg.eta}</td>
                <td>{leg.status}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
