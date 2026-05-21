import { postJson } from "./client";

export type ParseRallyRequest = {
  raw_text: string;
  event_name?: string;
  total_distance_km?: number;
  total_time_minutes?: number;
};

export type ParseRallyResponse = {
  event_name: string;
  trayek_name?: string | null;
  location?: string | null;
  normalized_text: string;
  total_distance_km?: number | null;
  total_time_minutes?: number | null;
  sub_trayek_count: number;
  waypoint_count: number;
  sub_trayeks: Array<{
    id: string;
    label: string;
    title: string;
    distance_km?: number | null;
    duration_minutes?: number | null;
    speed_mode: string;
    distance_counted_in_total: boolean;
    waypoints: Array<{ id: string; raw_text: string; ambiguous: boolean }>;
  }>;
  unresolved_tokens: Array<{ token: string; reason: string }>;
  warnings: string[];
  status: string;
  next_action: string;
};

export type PhotoOcrRequest = {
  photos: Array<{
    filename: string;
    mime_type?: string;
    image_base64?: string;
  }>;
  auto_parse?: boolean;
  auto_map_subtrayek?: boolean;
};

export type PhotoOcrResponse = {
  event_name: string;
  trayek_name: string;
  location: string;
  normalized_text: string;
  detected_total_distance_km?: number;
  detected_total_time_minutes?: number;
  photo_count: number;
  status: string;
  warnings: string[];
};

export const rallyApi = {
  parse(request: ParseRallyRequest) {
    return postJson<ParseRallyRequest, ParseRallyResponse>("/v1/rally/parse", request);
  },
  photoOcr(request: PhotoOcrRequest) {
    return postJson<PhotoOcrRequest, PhotoOcrResponse>("/v1/rally/photo-ocr", request);
  }
};
