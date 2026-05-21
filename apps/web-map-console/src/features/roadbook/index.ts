/**
 * Roadbook feature.
 *
 * Sumber data: `useRallyWorkspaceStore().roadbook` + `validation`.
 * Tampilan: `components/tables/RoadbookTable.tsx`.
 *
 * Modul ini menyediakan helper konversi dan formatter agar UI dan PDF export
 * memiliki tampilan konsisten.
 */

import type { RoadbookLeg, ValidationSummary } from "../../types/rally";

export type RoadbookColumn =
  | "no"
  | "subTrayek"
  | "from"
  | "to"
  | "instruction"
  | "distanceLeg"
  | "distanceCumulative"
  | "durationLeg"
  | "eta"
  | "speedTarget"
  | "status";

export const ROADBOOK_COLUMNS: RoadbookColumn[] = [
  "no",
  "subTrayek",
  "from",
  "to",
  "instruction",
  "distanceLeg",
  "distanceCumulative",
  "durationLeg",
  "eta",
  "speedTarget",
  "status",
];

export function formatKm(km: number): string {
  return km.toFixed(2).replace(".", ",") + " km";
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function summarizeRoadbook(legs: RoadbookLeg[]): {
  totalDistanceKm: number;
  totalDurationSeconds: number;
  hasViolation: boolean;
} {
  let totalDistanceKm = 0;
  let totalDurationSeconds = 0;
  let hasViolation = false;
  legs.forEach((leg) => {
    totalDistanceKm += leg.distanceKm;
    totalDurationSeconds += leg.durationSeconds;
    if (leg.status === "violation") hasViolation = true;
  });
  return { totalDistanceKm, totalDurationSeconds, hasViolation };
}

export function readinessBadge(validation?: ValidationSummary): {
  label: string;
  tone: "green" | "amber" | "red";
} {
  if (!validation) return { label: "Belum divalidasi", tone: "amber" };
  if (
    validation.distanceStatus === "compliant" &&
    validation.timeStatus === "compliant" &&
    validation.chainingStatus === "compliant"
  ) {
    return { label: "Siap lomba", tone: "green" };
  }
  if (
    validation.distanceStatus === "violation" ||
    validation.timeStatus === "violation" ||
    validation.chainingStatus === "violation"
  ) {
    return { label: "Belum layak", tone: "red" };
  }
  return { label: "Perlu review", tone: "amber" };
}
