import { create } from "zustand";
import type { ParseRallyResponse, PhotoOcrResponse } from "../api/rallyApi";
import type {
  Coordinate,
  MappedSubTrayekRoute,
  ProbabilityRouteOption,
  QuestionPhoto,
  RallyExecutionState,
  RallyWorkspace,
  RoadbookLeg,
  RouteEditMode,
  SubTrayekSpeedMode,
  SubTrayekTimingRow,
  TimingValidationStatus,
  TrayekTimingValidation,
  ValidationSummary
} from "../../types/rally";

type WorkspaceState = RallyWorkspace & {
  setRawText: (rawText: string) => void;
  setEventName: (eventName: string) => void;
  setMasterStartTime: (startTime: string) => void;
  processQuestionPhotos: (photos: Array<Pick<QuestionPhoto, "fileName" | "previewUrl">>) => void;
  setPhotoOcrResult: (result: PhotoOcrResponse) => void;
  applyParsedRally: (result: ParseRallyResponse) => void;
  selectSubTrayekRoute: (subTrayekId: string) => void;
  updateSubTrayekEndpoint: (subTrayekId: string, endpoint: "start" | "finish", value: string) => void;
  finishActiveSubTrayek: () => void;
  setRouteEditMode: (mode: RouteEditMode) => void;
  toggleSnapToRoad: () => void;
  selectProbabilityOption: (optionId: string) => void;
  acceptProbabilityOption: (optionId: string) => void;
  rejectProbabilityOption: (optionId: string) => void;
};

const DEFAULT_MASTER_START_TIME = "08:00";
const TRANSITION_WARNING_SECONDS = 60;

const emptyExecution: RallyExecutionState = {
  activeSubTrayekId: "",
  masterStartTime: DEFAULT_MASTER_START_TIME,
  masterFinishTime: DEFAULT_MASTER_START_TIME,
  totalDurationMinutes: 0,
  transitionWarningSeconds: TRANSITION_WARNING_SECONDS,
  roadbookReady: false
};

function parseClockMinutes(value: string) {
  const [hours = "0", minutes = "0"] = value.split(":");
  return Number(hours) * 60 + Number(minutes);
}

function formatClockFromMinutes(totalMinutes: number) {
  const normalized = ((Math.round(totalMinutes) % 1440) + 1440) % 1440;
  const hours = Math.floor(normalized / 60);
  const minutes = normalized % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function round2(value: number) {
  return Math.round(value * 100) / 100;
}

function kmPerSecond(speedKmh: number | null) {
  return speedKmh === null ? null : speedKmh / 3600;
}

function classifySpeedMode(mode: SubTrayekSpeedMode) {
  if (mode === "fixed_second") return "Kecepatan tetap detik";
  if (mode === "fixed_minute") return "Kecepatan tetap menit";
  if (mode === "average_speed") return "Kecepatan rata-rata";
  if (mode === "remaining_distance") return "Sisa jarak finish";
  if (mode === "free_time") return "Santai/bebas";
  return "Start/zero trip";
}

function coerceSpeedMode(mode: string): SubTrayekSpeedMode {
  if (
    mode === "fixed_second" ||
    mode === "fixed_minute" ||
    mode === "average_speed" ||
    mode === "remaining_distance" ||
    mode === "free_time"
  ) {
    return mode;
  }
  return "liaison_zero_trip";
}

function buildExecution(
  masterStartTime: string,
  totalDurationMinutes: number,
  routes: MappedSubTrayekRoute[],
  activeSubTrayekId?: string
): RallyExecutionState {
  const activeRoute = routes.find((route) => route.id === activeSubTrayekId) ?? routes[0];
  const activeIndex = activeRoute ? routes.findIndex((route) => route.id === activeRoute.id) : -1;
  const roadbookReady = routes.length > 0 && routes.every((route) => route.roadbookReady);

  return {
    activeSubTrayekId: activeRoute?.id ?? "",
    driverRunningSubTrayekId: activeRoute?.id,
    navigatorWorkingSubTrayekId: activeIndex >= 0 ? routes[activeIndex + 1]?.id : undefined,
    masterStartTime,
    masterFinishTime: formatClockFromMinutes(parseClockMinutes(masterStartTime) + totalDurationMinutes),
    totalDurationMinutes,
    transitionWarningSeconds: TRANSITION_WARNING_SECONDS,
    roadbookReady
  };
}

function buildRoadbookFromRoutes(routes: MappedSubTrayekRoute[]): RoadbookLeg[] {
  let cumulativeDistanceKm = 0;
  return routes
    .filter((route) => route.roadbookReady)
    .map((route) => {
      cumulativeDistanceKm += route.distanceKm ?? 0;
      return {
        id: `roadbook-${route.id}`,
        from: route.startLabel,
        to: route.finishLabel,
        instruction: `Sub ${route.sub}: start ${route.scheduledStartTime}, finish ${route.scheduledFinishTime}. ${route.routeSummary}`,
        distanceKm: route.distanceKm ?? 0,
        durationSeconds: route.durationMinutes * 60,
        cumulativeDistanceKm,
        eta: route.scheduledFinishTime,
        status: (route.mapStatus === "needs_review" ? "warning" : "ok") as RoadbookLeg["status"]
      };
    });
}

function buildValidationSummary(timing: TrayekTimingValidation): ValidationSummary {
  const distanceStatus =
    Math.abs(timing.distanceDeltaKm) <= timing.toleranceDistanceKm ? "compliant" : "warning";
  const timeStatus =
    Math.abs(timing.durationDeltaMinutes) <= timing.toleranceDurationMinutes ? "compliant" : "warning";
  const endpointBlocked = timing.rows.some((row) => row.needsUserStart || row.needsUserFinish);
  const score = timing.status === "valid" ? 94 : timing.status === "warning" ? 76 : 42;

  return {
    distanceStatus,
    timeStatus,
    chainingStatus: endpointBlocked ? "violation" : timing.rows.length > 0 ? "compliant" : "violation",
    score
  };
}

function routeExcerpt(rawWaypoints: string[]) {
  const excerpt = rawWaypoints.slice(0, 8).join(" - ");
  return excerpt || "Belum ada waypoint terbaca.";
}

function rowStatus(distanceKm: number | null, durationMinutes: number, endpointBlocked = false): TimingValidationStatus {
  if (durationMinutes <= 0) return "error";
  if (endpointBlocked) return "warning";
  if (distanceKm === null) return "warning";
  return "valid";
}

function buildScheduleFromParsed(result: ParseRallyResponse, masterStartTime: string) {
  const startMinutes = parseClockMinutes(masterStartTime);
  let cumulativeMinutes = 0;
  let calculatedDistanceKm = 0;
  let calculatedDurationMinutes = 0;

  const rows: SubTrayekTimingRow[] = result.sub_trayeks.map((subTrayek) => {
    const distanceKm = subTrayek.distance_km ?? null;
    const durationMinutes = subTrayek.duration_minutes ?? 0;
    const speedKmh =
      distanceKm !== null && durationMinutes > 0 ? round2((distanceKm / durationMinutes) * 60) : null;
    const speedMode = coerceSpeedMode(subTrayek.speed_mode);
    const cumulativeStartMinutes = cumulativeMinutes;
    const cumulativeFinishMinutes = cumulativeStartMinutes + durationMinutes;
    const rawWaypoints = subTrayek.waypoints.map((waypoint) => waypoint.raw_text);
    const startRawText = subTrayek.start_raw_text ?? rawWaypoints[0] ?? null;
    const finishRawText = subTrayek.finish_raw_text ?? rawWaypoints[rawWaypoints.length - 1] ?? null;
    const endpointBlocked = subTrayek.needs_user_start || subTrayek.needs_user_finish;

    if (subTrayek.distance_counted_in_total && distanceKm !== null) {
      calculatedDistanceKm += distanceKm;
    }
    calculatedDurationMinutes += durationMinutes;
    cumulativeMinutes = cumulativeFinishMinutes;

    const notes = [
      ...(distanceKm === null ? ["Jarak sub-trayek belum terbaca eksplisit."] : []),
      ...(durationMinutes <= 0 ? ["Durasi sub-trayek belum terbaca."] : []),
      ...(subTrayek.needs_user_start ? ["Start wajib diisi navigator sebelum mapping/routing."] : []),
      ...(subTrayek.needs_user_finish ? ["Finish wajib diisi navigator sebelum mapping/routing."] : []),
      ...(subTrayek.start_status === "inherited" ? ["Start diwarisi dari finish sub sebelumnya."] : []),
      ...subTrayek.waypoints
        .filter((waypoint) => waypoint.ambiguous)
        .map((waypoint) => `Waypoint ambigu: ${waypoint.raw_text}`)
    ];

    return {
      id: subTrayek.id,
      sub: subTrayek.label,
      title: subTrayek.title || `Sub ${subTrayek.label}`,
      declaredDistanceKm: distanceKm,
      declaredDurationMinutes: durationMinutes,
      distanceCountedInTotal: subTrayek.distance_counted_in_total,
      calculatedSpeedKmh: speedKmh,
      kmPerSecond: kmPerSecond(speedKmh),
      speedMode,
      classificationLabel: classifySpeedMode(speedMode),
      scheduledStartTime: formatClockFromMinutes(startMinutes + cumulativeStartMinutes),
      scheduledFinishTime: formatClockFromMinutes(startMinutes + cumulativeFinishMinutes),
      cumulativeStartMinutes,
      cumulativeFinishMinutes,
      routeTextExcerpt: routeExcerpt(rawWaypoints),
      startRawText,
      finishRawText,
      startStatus: subTrayek.start_status,
      finishStatus: subTrayek.finish_status,
      needsUserStart: subTrayek.needs_user_start,
      needsUserFinish: subTrayek.needs_user_finish,
      status: rowStatus(distanceKm, durationMinutes, endpointBlocked),
      notes
    };
  });

  const declaredDistanceKm = result.total_distance_km ?? round2(calculatedDistanceKm);
  const declaredDurationMinutes = result.total_time_minutes ?? calculatedDurationMinutes;
  const parserWarnings = [
    ...result.warnings,
    ...result.unresolved_tokens.map((token) => `${token.token}: ${token.reason}`)
  ];
  const hasRowIssue = rows.some((row) => row.status !== "valid");
  const hasDistanceDelta = Math.abs(round2(calculatedDistanceKm) - declaredDistanceKm) > 0.05;
  const hasDurationDelta = calculatedDurationMinutes !== declaredDurationMinutes;

  const timingValidation: TrayekTimingValidation = {
    trayekId: result.trayek_name ?? result.event_name,
    declaredDistanceKm,
    declaredDurationMinutes,
    calculatedDistanceKm: round2(calculatedDistanceKm),
    calculatedDurationMinutes,
    distanceDeltaKm: round2(calculatedDistanceKm - declaredDistanceKm),
    durationDeltaMinutes: calculatedDurationMinutes - declaredDurationMinutes,
    toleranceDistanceKm: 0.05,
    toleranceDurationMinutes: 0,
    status: parserWarnings.length > 0 || hasRowIssue || hasDistanceDelta || hasDurationDelta ? "warning" : "valid",
    rows,
    warnings: parserWarnings
  };

  const mappedSubTrayeks: MappedSubTrayekRoute[] = result.sub_trayeks.map((subTrayek, index) => {
    const row = rows[index];
    const rawWaypoints = subTrayek.waypoints.map((waypoint) => waypoint.raw_text);
    const startLabel = subTrayek.start_raw_text ?? rawWaypoints[0] ?? `Sub ${subTrayek.label} start`;
    const finishLabel = subTrayek.finish_raw_text ?? rawWaypoints[rawWaypoints.length - 1] ?? `Sub ${subTrayek.label} finish`;
    const endpointBlocked = subTrayek.needs_user_start || subTrayek.needs_user_finish;

    return {
      id: subTrayek.id,
      sub: row.sub,
      title: row.title,
      startLabel,
      finishLabel,
      startStatus: subTrayek.start_status,
      finishStatus: subTrayek.finish_status,
      needsUserStart: subTrayek.needs_user_start,
      needsUserFinish: subTrayek.needs_user_finish,
      distanceKm: row.declaredDistanceKm,
      durationMinutes: row.declaredDurationMinutes,
      speedKmh: row.calculatedSpeedKmh,
      kmPerSecond: row.kmPerSecond,
      speedMode: row.speedMode,
      scheduledStartTime: row.scheduledStartTime,
      scheduledFinishTime: row.scheduledFinishTime,
      cumulativeStartMinutes: row.cumulativeStartMinutes,
      cumulativeFinishMinutes: row.cumulativeFinishMinutes,
      waypointCount: subTrayek.waypoints.length,
      mapStatus: endpointBlocked || subTrayek.waypoints.length === 0 ? "needs_review" : "ocr_ready",
      geometry: [] as Coordinate[],
      routeSummary:
        endpointBlocked
          ? "Start/finish belum lengkap. Isi endpoint sebelum generate peta final."
          : subTrayek.start_status === "inherited"
            ? `Start diwarisi dari finish sub sebelumnya: ${startLabel}. ${routeExcerpt(rawWaypoints)}`
            : subTrayek.waypoints.length > 0
              ? `Waypoint OCR siap di-resolve koordinat: ${routeExcerpt(rawWaypoints)}`
              : "Belum ada waypoint untuk di-resolve.",
      roadbookReady: false
    };
  });

  return {
    timingValidation,
    mappedSubTrayeks,
    execution: buildExecution(masterStartTime, declaredDurationMinutes, mappedSubTrayeks),
    validation: buildValidationSummary(timingValidation)
  };
}

function rescheduleRows(rows: SubTrayekTimingRow[], masterStartTime: string) {
  const startMinutes = parseClockMinutes(masterStartTime);
  let cumulativeMinutes = 0;

  return rows.map((row) => {
    const cumulativeStartMinutes = cumulativeMinutes;
    const cumulativeFinishMinutes = cumulativeStartMinutes + row.declaredDurationMinutes;
    cumulativeMinutes = cumulativeFinishMinutes;

    return {
      ...row,
      scheduledStartTime: formatClockFromMinutes(startMinutes + cumulativeStartMinutes),
      scheduledFinishTime: formatClockFromMinutes(startMinutes + cumulativeFinishMinutes),
      cumulativeStartMinutes,
      cumulativeFinishMinutes
    };
  });
}

function rescheduleRoutes(routes: MappedSubTrayekRoute[], rows: SubTrayekTimingRow[]) {
  const rowById = new Map(rows.map((row) => [row.id, row]));
  return routes.map((route) => {
    const row = rowById.get(route.id);
    return row
      ? {
          ...route,
          scheduledStartTime: row.scheduledStartTime,
          scheduledFinishTime: row.scheduledFinishTime,
          cumulativeStartMinutes: row.cumulativeStartMinutes,
          cumulativeFinishMinutes: row.cumulativeFinishMinutes
        }
      : route;
  });
}

function statusFromPhotoOcr(result: PhotoOcrResponse) {
  if (result.status === "failed") return "failed" as const;
  if (result.normalized_text.trim().length > 0) return "parsed" as const;
  return "needs_review" as const;
}

export const useRallyWorkspaceStore = create<WorkspaceState>((set) => ({
  eventName: "Belum ada event",
  rawText: "",
  waypoints: [],
  roadbook: [],
  validation: undefined,
  timingValidation: undefined,
  mappedSubTrayeks: [],
  execution: emptyExecution,
  photoOcr: {
    status: "idle",
    photos: [],
    lastMessage: "Upload foto soal atau tempel teks untuk mulai validasi.",
    detectedFields: {}
  },
  routeEditor: {
    mode: "inspect",
    snapToRoad: true,
    routeLocked: false,
    selectedSubTrayekId: undefined
  },
  probabilityOptions: [],
  selectedProbabilityOptionId: undefined,
  setRawText: (rawText) => set({ rawText }),
  setEventName: (eventName) => set({ eventName }),
  setMasterStartTime: (masterStartTime) =>
    set((state) => {
      if (!state.timingValidation) {
        return {
          execution: {
            ...state.execution,
            masterStartTime,
            masterFinishTime: formatClockFromMinutes(
              parseClockMinutes(masterStartTime) + state.execution.totalDurationMinutes
            )
          }
        };
      }

      const rows = rescheduleRows(state.timingValidation.rows, masterStartTime);
      const mappedSubTrayeks = rescheduleRoutes(state.mappedSubTrayeks, rows);
      const timingValidation = { ...state.timingValidation, rows };
      const execution = buildExecution(
        masterStartTime,
        timingValidation.declaredDurationMinutes,
        mappedSubTrayeks,
        state.execution.activeSubTrayekId
      );

      return {
        timingValidation,
        mappedSubTrayeks,
        execution,
        roadbook: buildRoadbookFromRoutes(mappedSubTrayeks)
      };
    }),
  processQuestionPhotos: (photos) =>
    set((state) => ({
      photoOcr: {
        ...state.photoOcr,
        status: "photo_ready",
        photos: photos.map((photo, index) => ({
          id: `photo-${index + 1}`,
          fileName: photo.fileName,
          previewUrl: photo.previewUrl,
          pageRole: "unknown",
          ocrConfidence: 0,
          status: "photo_ready"
        })),
        lastMessage: "Foto diterima. Menunggu OCR backend menghasilkan teks."
      }
    })),
  setPhotoOcrResult: (result) =>
    set((state) => ({
      eventName: result.event_name || state.eventName,
      rawText: result.normalized_text || state.rawText,
      photoOcr: {
        ...state.photoOcr,
        status: statusFromPhotoOcr(result),
        eventName: result.event_name || undefined,
        trayekName: result.trayek_name || undefined,
        location: result.location || undefined,
        lastMessage:
          result.warnings.length > 0
            ? result.warnings.join(" ")
            : result.normalized_text
              ? "OCR selesai. Lanjutkan parse teks untuk validasi sub-trayek."
              : "OCR worker belum tersedia. Tempel hasil OCR manual ke panel soal.",
        detectedFields: {
          eventName: result.event_name || undefined,
          trayekName: result.trayek_name || undefined,
          location: result.location || undefined,
          totalDistanceKm: result.detected_total_distance_km,
          totalTimeMinutes: result.detected_total_time_minutes
        }
      }
    })),
  applyParsedRally: (result) =>
    set((state) => {
      const scheduleState = buildScheduleFromParsed(result, state.execution.masterStartTime);
      return {
        eventName: result.event_name || state.eventName,
        rawText: result.normalized_text || state.rawText,
        ...scheduleState,
        roadbook: [],
        routeEditor: {
          ...state.routeEditor,
          selectedSubTrayekId: scheduleState.execution.activeSubTrayekId
        },
        photoOcr: {
          ...state.photoOcr,
          status: scheduleState.timingValidation.status === "valid" ? "timing_validated" : "needs_review",
          eventName: result.event_name || undefined,
          trayekName: result.trayek_name || undefined,
          location: result.location || undefined,
          lastMessage:
            result.status === "parsed"
              ? "Soal berhasil diparse. Review timing, waypoint ambigu, lalu resolve koordinat."
              : result.next_action,
          detectedFields: {
            ...state.photoOcr.detectedFields,
            eventName: result.event_name || undefined,
            trayekName: result.trayek_name || undefined,
            location: result.location || undefined,
            totalDistanceKm: result.total_distance_km ?? undefined,
            totalTimeMinutes: result.total_time_minutes ?? undefined
          }
        }
      };
    }),
  selectSubTrayekRoute: (subTrayekId) =>
    set((state) => ({
      execution: {
        ...state.execution,
        activeSubTrayekId: subTrayekId
      },
      routeEditor: {
        ...state.routeEditor,
        selectedSubTrayekId: subTrayekId
      }
    })),
  updateSubTrayekEndpoint: (subTrayekId, endpoint, value) =>
    set((state) => {
      const cleanValue = value.trim();
      const isReady = cleanValue.length > 0;
      const timingRows = state.timingValidation?.rows.map((row) => {
        if (row.id !== subTrayekId) return row;
        const nextRow = {
          ...row,
          ...(endpoint === "start"
            ? {
                startRawText: cleanValue || null,
                startStatus: isReady ? "explicit" : "missing",
                needsUserStart: !isReady
              }
            : {
                finishRawText: cleanValue || null,
                finishStatus: isReady ? "explicit" : "missing",
                needsUserFinish: !isReady
              })
        };
        return {
          ...nextRow,
          status: rowStatus(
            nextRow.declaredDistanceKm,
            nextRow.declaredDurationMinutes,
            nextRow.needsUserStart || nextRow.needsUserFinish
          )
        };
      });

      const mappedSubTrayeks: MappedSubTrayekRoute[] = state.mappedSubTrayeks.map((route) => {
        if (route.id !== subTrayekId) return route;
        const nextRoute = {
          ...route,
          ...(endpoint === "start"
            ? {
                startLabel: cleanValue,
                startStatus: isReady ? "explicit" : "missing",
                needsUserStart: !isReady
              }
            : {
                finishLabel: cleanValue,
                finishStatus: isReady ? "explicit" : "missing",
                needsUserFinish: !isReady
              })
        };
        const endpointBlocked = nextRoute.needsUserStart || nextRoute.needsUserFinish;
        return {
          ...nextRoute,
          mapStatus: endpointBlocked ? "needs_review" : "ocr_ready" as MappedSubTrayekRoute["mapStatus"],
          routeSummary: endpointBlocked
            ? "Start/finish belum lengkap. Isi endpoint sebelum generate peta final."
            : "Endpoint sudah lengkap. Waypoint siap di-resolve koordinat."
        };
      });

      const timingValidation = state.timingValidation && timingRows
        ? {
            ...state.timingValidation,
            rows: timingRows,
            status: timingRows.some((row) => row.status !== "valid") ? "warning" as const : state.timingValidation.status
          }
        : state.timingValidation;

      return {
        timingValidation,
        mappedSubTrayeks,
        validation: timingValidation ? buildValidationSummary(timingValidation) : state.validation,
        roadbook: buildRoadbookFromRoutes(mappedSubTrayeks)
      };
    }),
  finishActiveSubTrayek: () =>
    set((state) => {
      const activeIndex = state.mappedSubTrayeks.findIndex(
        (route) => route.id === state.execution.activeSubTrayekId
      );
      if (activeIndex < 0) {
        return state;
      }

      const mappedSubTrayeksNext = state.mappedSubTrayeks.map((route, index) =>
        index === activeIndex
          ? {
              ...route,
              mapStatus: "finished" as const,
              roadbookReady: true
            }
          : route
      );
      const nextRoute = mappedSubTrayeksNext[activeIndex + 1];
      const roadbook = buildRoadbookFromRoutes(mappedSubTrayeksNext);
      const roadbookReady =
        mappedSubTrayeksNext.length > 0 && mappedSubTrayeksNext.every((route) => route.roadbookReady);

      return {
        mappedSubTrayeks: mappedSubTrayeksNext,
        roadbook,
        photoOcr: {
          ...state.photoOcr,
          status: roadbookReady ? "roadbook_ready" : "mapping_subtrayek",
          lastMessage: roadbookReady
            ? "Semua sub-trayek selesai divalidasi dan roadbook siap dipakai."
            : `Sub ${mappedSubTrayeksNext[activeIndex]?.sub ?? ""} selesai. Navigator bisa lanjut review sub ${
                nextRoute?.sub ?? "berikutnya"
              }.`
        },
        execution: {
          ...state.execution,
          activeSubTrayekId: nextRoute?.id ?? state.execution.activeSubTrayekId,
          driverRunningSubTrayekId: nextRoute?.id ?? state.execution.driverRunningSubTrayekId,
          navigatorWorkingSubTrayekId: mappedSubTrayeksNext[activeIndex + 2]?.id,
          roadbookReady
        },
        routeEditor: {
          ...state.routeEditor,
          selectedSubTrayekId: nextRoute?.id ?? state.routeEditor.selectedSubTrayekId
        }
      };
    }),
  setRouteEditMode: (mode) =>
    set((state) => ({
      routeEditor: {
        ...state.routeEditor,
        mode
      }
    })),
  toggleSnapToRoad: () =>
    set((state) => ({
      routeEditor: {
        ...state.routeEditor,
        snapToRoad: !state.routeEditor.snapToRoad
      }
    })),
  selectProbabilityOption: (optionId) => set({ selectedProbabilityOptionId: optionId }),
  acceptProbabilityOption: (optionId) =>
    set((state) => ({
      selectedProbabilityOptionId: optionId,
      probabilityOptions: state.probabilityOptions.map((option) => ({
        ...option,
        status: option.id === optionId ? "accepted" : option.status
      }))
    })),
  rejectProbabilityOption: (optionId) =>
    set((state) => ({
      probabilityOptions: state.probabilityOptions.map((option) => ({
        ...option,
        status: option.id === optionId ? "rejected" : option.status
      }))
    }))
}));
