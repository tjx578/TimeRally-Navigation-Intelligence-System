import { postJson } from "./client";

export type InferMissingWaypointRequest = {
  event_id?: string;
  context: {
    missing_waypoint_text: string;
    previous_waypoint_id: string;
    next_waypoint_id: string;
    target_distance_km?: number;
    target_time_seconds?: number;
    navigation_action?: string;
    landmark_type_hint?: string;
  };
  max_candidates?: number;
};

export type RouteEditOperationRequest = {
  event_id: string;
  sub_trayek_id?: string;
  leg_id?: string;
  operation: "draw" | "erase" | "repair" | "split" | "lock";
  snap_to_road: boolean;
  geometry: Array<{ lat: number; lng: number }>;
  reason?: string;
};

export const probabilityApi = {
  inferMissingWaypoint(request: InferMissingWaypointRequest) {
    return postJson<InferMissingWaypointRequest, unknown>(
      "/v1/probability/infer-missing-waypoint",
      request
    );
  },
  applyRouteEdit(request: RouteEditOperationRequest) {
    return postJson<RouteEditOperationRequest, unknown>("/v1/probability/route-edit", request);
  }
};

