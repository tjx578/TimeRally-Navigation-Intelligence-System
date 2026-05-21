/**
 * Export center feature.
 *
 * Membantu UI memilih format export, memanggil /v1/export/artifacts,
 * dan menampilkan link unduh.
 */

import { postJson } from "../../lib/api/client";

export type ExportFormat = "yaml" | "gpx" | "kml" | "geojson" | "roadbook" | "validation-report" | "candidate-review";

export interface ExportRequest {
  event_id: string;
  formats: ExportFormat[];
  include_validation_report?: boolean;
  include_candidate_review?: boolean;
}

export interface ExportArtifactInfo {
  format: string;
  path: string;
  status: string;
}

export interface ExportResponse {
  event_id: string;
  artifacts: ExportArtifactInfo[];
  status: string;
}

export const DEFAULT_FORMATS: ExportFormat[] = ["yaml", "gpx", "kml", "geojson", "roadbook"];

export async function createExport(req: ExportRequest): Promise<ExportResponse> {
  return postJson<ExportRequest, ExportResponse>("/v1/export/artifacts", req);
}

export function describeFormat(fmt: ExportFormat): { label: string; description: string } {
  switch (fmt) {
    case "yaml":
      return { label: "Event YAML", description: "Struktur sub-trayek + waypoint untuk arsip lomba." };
    case "gpx":
      return { label: "GPX", description: "Untuk GPS handheld dan Organic Maps." };
    case "kml":
      return { label: "KML", description: "Untuk Google Earth / My Maps." };
    case "geojson":
      return { label: "GeoJSON", description: "Untuk MapLibre layer & QGIS analysis." };
    case "roadbook":
      return { label: "Roadbook Markdown", description: "Bisa dicetak / disertakan ke field-mobile." };
    case "validation-report":
      return { label: "Validation Report", description: "Hasil constraint engine end-to-end." };
    case "candidate-review":
      return { label: "Candidate Review", description: "Hasil probability resolver yang butuh approval." };
  }
}
