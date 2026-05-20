export type Coordinate = {
  lat: number;
  lng: number;
};

export type SourceStatus =
  | "verified_local"
  | "verified_kmpal"
  | "verified_osm"
  | "verified_google_online"
  | "inferred_high_confidence"
  | "inferred_low_confidence"
  | "unresolved";

export type Waypoint = {
  id: string;
  label: string;
  instruction: string;
  coordinate?: Coordinate;
  status: SourceStatus;
  confidence: number;
  source?: string;
};

export type RoadbookLeg = {
  id: string;
  from: string;
  to: string;
  instruction: string;
  distanceKm: number;
  durationSeconds: number;
  cumulativeDistanceKm: number;
  eta: string;
  status: "ok" | "warning" | "violation";
};

export type ValidationSummary = {
  distanceStatus: "compliant" | "warning" | "violation";
  timeStatus: "compliant" | "warning" | "violation";
  chainingStatus: "compliant" | "warning" | "violation";
  score: number;
};

export type RouteEditMode = "inspect" | "draw" | "erase" | "repair" | "split" | "lock";

export type ProbabilityRouteOption = {
  id: string;
  label: string;
  missingWaypointLabel: string;
  confidence: number;
  distanceDeviationPercent: number;
  timeDeviationSeconds: number;
  routeCorridorFit: number;
  landmarkFit: number;
  turnGeometryFit: number;
  provider: string;
  status: "recommended" | "review" | "rejected" | "accepted";
  reasons: string[];
};

export type RouteEditorState = {
  mode: RouteEditMode;
  snapToRoad: boolean;
  selectedSubTrayekId?: string;
  selectedLegId?: string;
  routeLocked: boolean;
};

export type SubTrayekSpeedMode =
  | "liaison_zero_trip"
  | "average_speed"
  | "fixed_second"
  | "remaining_distance";

export type TimingValidationStatus = "valid" | "warning" | "error" | "unchecked";

export type SubTrayekTimingRow = {
  id: string;
  sub: string;
  title: string;
  declaredDistanceKm: number | null;
  inferredDistanceKm?: number;
  declaredDurationMinutes: number;
  distanceCountedInTotal: boolean;
  calculatedSpeedKmh: number | null;
  kmPerSecond: number | null;
  speedMode: SubTrayekSpeedMode;
  classificationLabel: string;
  scheduledStartTime: string;
  scheduledFinishTime: string;
  cumulativeStartMinutes: number;
  cumulativeFinishMinutes: number;
  routeTextExcerpt: string;
  status: TimingValidationStatus;
  notes: string[];
};

export type TrayekTimingValidation = {
  trayekId: string;
  declaredDistanceKm: number;
  declaredDurationMinutes: number;
  calculatedDistanceKm: number;
  calculatedDurationMinutes: number;
  distanceDeltaKm: number;
  durationDeltaMinutes: number;
  toleranceDistanceKm: number;
  toleranceDurationMinutes: number;
  status: TimingValidationStatus;
  rows: SubTrayekTimingRow[];
  warnings: string[];
};

export type OcrWorkflowStatus =
  | "idle"
  | "photo_ready"
  | "preprocessing"
  | "ocr_running"
  | "parsed"
  | "timing_validated"
  | "mapping_subtrayek"
  | "roadbook_ready"
  | "needs_review"
  | "failed";

export type QuestionPhoto = {
  id: string;
  fileName: string;
  previewUrl?: string;
  pageRole: "intro" | "subtrayek_a_d" | "subtrayek_e_g" | "unknown";
  ocrConfidence: number;
  status: OcrWorkflowStatus;
};

export type PhotoOcrWorkflow = {
  status: OcrWorkflowStatus;
  photos: QuestionPhoto[];
  eventName?: string;
  trayekName?: string;
  location?: string;
  lastMessage: string;
  detectedFields: {
    eventName?: string;
    trayekName?: string;
    location?: string;
    totalDistanceKm?: number;
    totalTimeMinutes?: number;
    headerDistanceCorrectionKm?: number;
  };
};

export type SubTrayekMapStatus =
  | "ocr_ready"
  | "timing_valid"
  | "mapping"
  | "mapped"
  | "needs_review"
  | "finished";

export type MappedSubTrayekRoute = {
  id: string;
  sub: string;
  title: string;
  startLabel: string;
  finishLabel: string;
  distanceKm: number | null;
  durationMinutes: number;
  speedKmh: number | null;
  kmPerSecond: number | null;
  speedMode: SubTrayekSpeedMode;
  scheduledStartTime: string;
  scheduledFinishTime: string;
  cumulativeStartMinutes: number;
  cumulativeFinishMinutes: number;
  waypointCount: number;
  mapStatus: SubTrayekMapStatus;
  geometry: Coordinate[];
  routeSummary: string;
  roadbookReady: boolean;
};

export type RallyExecutionState = {
  activeSubTrayekId: string;
  driverRunningSubTrayekId?: string;
  navigatorWorkingSubTrayekId?: string;
  masterStartTime: string;
  masterFinishTime: string;
  totalDurationMinutes: number;
  transitionWarningSeconds: number;
  roadbookReady: boolean;
};

export type RallyWorkspace = {
  eventName: string;
  rawText: string;
  waypoints: Waypoint[];
  roadbook: RoadbookLeg[];
  validation?: ValidationSummary;
  timingValidation?: TrayekTimingValidation;
  photoOcr: PhotoOcrWorkflow;
  mappedSubTrayeks: MappedSubTrayekRoute[];
  execution: RallyExecutionState;
  routeEditor: RouteEditorState;
  probabilityOptions: ProbabilityRouteOption[];
  selectedProbabilityOptionId?: string;
};
