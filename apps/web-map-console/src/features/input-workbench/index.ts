/**
 * Input workbench feature.
 *
 * Menerima raw text, OCR, PDF, gambar, spreadsheet, KML/GPX, dan menormalisasi
 * sebelum dikirim ke /v1/rally/parse.
 */

import { rallyApi, type ParseRallyResponse } from "../../lib/api/rallyApi";

export type InputKind = "raw_text" | "ocr_text" | "pdf" | "image" | "spreadsheet" | "kml" | "gpx";

export interface InputPayload {
  kind: InputKind;
  filename?: string;
  rawText: string;
  eventName?: string;
  totalDistanceKm?: number;
  totalTimeMinutes?: number;
}

/**
 * Bersihkan input pengguna:
 *  - hilangkan baris kosong berlebihan,
 *  - rapikan whitespace,
 *  - pertahankan case (BR vs br sangat penting di rally).
 */
export function normalizeRawText(input: string): string {
  return input
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.replace(/[ \t]+$/g, "").replace(/[ \t]{2,}/g, " "))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export async function submitParse(payload: InputPayload): Promise<ParseRallyResponse> {
  const cleaned = normalizeRawText(payload.rawText);
  return rallyApi.parse({
    raw_text: cleaned,
    event_name: payload.eventName,
    total_distance_km: payload.totalDistanceKm,
    total_time_minutes: payload.totalTimeMinutes,
  });
}

export function describeParseStatus(response: ParseRallyResponse): {
  tone: "green" | "amber" | "red";
  message: string;
} {
  if (response.status === "ok") {
    return {
      tone: "green",
      message: `Berhasil: ${response.sub_trayek_count} sub trayek, ${response.waypoint_count} waypoint.`,
    };
  }
  if (response.status === "warning") {
    return {
      tone: "amber",
      message: `Selesai dengan peringatan. ${response.next_action}.`,
    };
  }
  return { tone: "red", message: `Belum siap: ${response.next_action}.` };
}
