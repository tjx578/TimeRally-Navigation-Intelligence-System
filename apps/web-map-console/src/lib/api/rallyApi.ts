import { postJson } from "./client";

export type ParseRallyRequest = {
  raw_text: string;
  event_name?: string;
  total_distance_km?: number;
  total_time_minutes?: number;
};

export type ParseRallyResponse = {
  event_name: string;
  normalized_text: string;
  sub_trayek_count: number;
  waypoint_count: number;
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
