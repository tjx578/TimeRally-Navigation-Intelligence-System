/**
 * Route editor feature.
 *
 * Mengelola operasi edit rute manual: draw, snap, lock, repair, split.
 * Operasi dikirim ke /v1/probability/route-edit.
 */

import { postJson } from "../../lib/api/client";
import type { RouteEditMode, RouteEditorState } from "../../types/rally";

export interface RouteEditOperation {
  event_id: string;
  sub_trayek_id?: string;
  leg_id?: string;
  operation: RouteEditMode;
  snap_to_road?: boolean;
  geometry?: Array<{ lat: number; lng: number }>;
  reason?: string;
}

export interface RouteEditResponse {
  operation_id: string;
  affected_leg_ids: string[];
  requires_revalidation: boolean;
  status: string;
}

export async function applyRouteEdit(operation: RouteEditOperation): Promise<RouteEditResponse> {
  return postJson<RouteEditOperation, RouteEditResponse>("/v1/probability/route-edit", operation);
}

export const DEFAULT_EDITOR_STATE: RouteEditorState = {
  mode: "inspect",
  snapToRoad: true,
  routeLocked: false,
};

export function nextMode(state: RouteEditorState, mode: RouteEditMode): RouteEditorState {
  if (state.routeLocked && mode !== "inspect" && mode !== "lock") {
    return state;
  }
  return { ...state, mode };
}

export function describeMode(mode: RouteEditMode): string {
  switch (mode) {
    case "inspect":
      return "Inspeksi (read-only)";
    case "draw":
      return "Gambar segmen baru";
    case "erase":
      return "Hapus segmen / waypoint";
    case "repair":
      return "Sambungkan ulang chain";
    case "split":
      return "Pisah sub-trayek";
    case "lock":
      return "Kunci rute - tidak dapat diedit";
  }
}
