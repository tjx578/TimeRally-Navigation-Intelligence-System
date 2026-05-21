/**
 * Sub trayek map review feature.
 *
 * Membantu navigator mengkonfirmasi setiap sub-trayek di peta sebelum
 * roadbook dianggap siap.
 */

import type { MappedSubTrayekRoute, SubTrayekMapStatus } from "../../types/rally";

export function aggregateMapStatuses(routes: MappedSubTrayekRoute[]): {
  total: number;
  mapped: number;
  needsReview: number;
  finished: number;
  status: SubTrayekMapStatus;
} {
  const total = routes.length;
  const mapped = routes.filter((r) => r.mapStatus === "mapped").length;
  const needsReview = routes.filter((r) => r.mapStatus === "needs_review").length;
  const finished = routes.filter((r) => r.mapStatus === "finished").length;
  let status: SubTrayekMapStatus = "ocr_ready";
  if (finished === total && total > 0) status = "finished";
  else if (needsReview > 0) status = "needs_review";
  else if (mapped > 0) status = "mapped";
  else if (total > 0) status = "mapping";
  return { total, mapped, needsReview, finished, status };
}

export function markRoadbookReady(routes: MappedSubTrayekRoute[]): MappedSubTrayekRoute[] {
  return routes.map((r) => ({ ...r, roadbookReady: r.mapStatus === "finished" }));
}
