import { create } from "zustand";
import type {
  Coordinate,
  MappedSubTrayekRoute,
  ProbabilityRouteOption,
  QuestionPhoto,
  RallyWorkspace,
  RoadbookLeg,
  RouteEditMode,
  SubTrayekSpeedMode,
  SubTrayekTimingRow,
  TrayekTimingValidation
} from "../../types/rally";

type WorkspaceState = RallyWorkspace & {
  setRawText: (rawText: string) => void;
  setEventName: (eventName: string) => void;
  setMasterStartTime: (startTime: string) => void;
  processQuestionPhotos: (photos: Array<Pick<QuestionPhoto, "fileName" | "previewUrl">>) => void;
  selectSubTrayekRoute: (subTrayekId: string) => void;
  finishActiveSubTrayek: () => void;
  setRouteEditMode: (mode: RouteEditMode) => void;
  toggleSnapToRoad: () => void;
  selectProbabilityOption: (optionId: string) => void;
  acceptProbabilityOption: (optionId: string) => void;
  rejectProbabilityOption: (optionId: string) => void;
};

type TimingSeed = {
  id: string;
  sub: string;
  title: string;
  declaredDistanceKm: number | null;
  inferredDistanceKm?: number;
  declaredDurationMinutes: number;
  distanceCountedInTotal: boolean;
  calculatedSpeedKmh: number | null;
  speedMode: SubTrayekSpeedMode;
  routeTextExcerpt: string;
  status: SubTrayekTimingRow["status"];
  notes: string[];
};

type RouteSeed = {
  id: string;
  startLabel: string;
  finishLabel: string;
  waypointCount: number;
  mapStatus: MappedSubTrayekRoute["mapStatus"];
  geometry: Coordinate[];
  routeSummary: string;
};

const DEFAULT_MASTER_START_TIME = "08:00";
const TRANSITION_WARNING_SECONDS = 60;

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

function kmPerSecond(speedKmh: number | null) {
  return speedKmh === null ? null : speedKmh / 3600;
}

function classifySpeedMode(mode: SubTrayekSpeedMode) {
  if (mode === "fixed_second") return "Kecepatan tetap detik";
  if (mode === "average_speed") return "Kecepatan rata-rata";
  if (mode === "remaining_distance") return "Sisa jarak finish";
  return "Start/zero trip";
}

const timingSeeds: TimingSeed[] = [
  {
    id: "sub-a-zero-trip",
    sub: "A",
    title: "INNA Bali Heritage ke Tangguntiti Tonja",
    declaredDistanceKm: null,
    inferredDistanceKm: 3.57,
    declaredDurationMinutes: 12,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 17.86,
    speedMode: "average_speed",
    routeTextExcerpt: "Start dari INNA BALI HERITAGE Hotel (Zero) - Jl. Patimura - Jl. Suli - Jl. Nangka - BR. Tangguntiti Tonja.",
    status: "warning",
    notes: ["Jarak tidak tertulis di sub A dan diambil dari selisih total dikurangi sub B-G."]
  },
  {
    id: "sub-b-penarungan",
    sub: "B",
    title: "Tangguntiti Tonja ke X Penarungan",
    declaredDistanceKm: 12.46,
    declaredDurationMinutes: 38,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 19.67,
    speedMode: "average_speed",
    routeTextExcerpt: "BR. Pengukuh - BR. Cabe - SD No. 1 Darmasaba - BKR di LR - Jl. Carik Aban - BR. Blungbang.",
    status: "valid",
    notes: ["Jarak dihitung dari kecepatan 19,67 km/jam x 38 menit."]
  },
  {
    id: "sub-c-bongkasa",
    sub: "C",
    title: "Penarungan ke Tohpati",
    declaredDistanceKm: 24.87,
    declaredDurationMinutes: 75,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 19.9,
    speedMode: "fixed_second",
    routeTextExcerpt: "BR. Dajan Peken - Baha/Mengwi - Sangeh - Bongkasa - Kutaraga - BR. Tohpati.",
    status: "valid",
    notes: ["Sub C memiliki jarak eksplisit 24,87 km."]
  },
  {
    id: "sub-d-kedewatan",
    sub: "D",
    title: "Tohpati ke Perbekel Melinggih Kelod",
    declaredDistanceKm: 11.73,
    declaredDurationMinutes: 45,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 15.64,
    speedMode: "average_speed",
    routeTextExcerpt: "Arah Ubud/Gianyar - IJU - BKR di UJ - BR. Pande - BR. Kedewatan - Perbekel Melinggih Kelod.",
    status: "valid",
    notes: ["Jarak dihitung dari kecepatan 15,64 km/jam x 45 menit."]
  },
  {
    id: "sub-e-manukaya",
    sub: "E",
    title: "Melinggih Kelod ke SDN 4 Manukaya",
    declaredDistanceKm: 21.9,
    declaredDurationMinutes: 50,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 26.28,
    speedMode: "average_speed",
    routeTextExcerpt: "BR. Pengaji - SDN. 2 Kelusa - Perbekel Brasela - Tegallalang - Sebatu - Jl. Sentanu - Jl. Tirta.",
    status: "valid",
    notes: ["Sub E merupakan halaman lanjutan foto kedua."]
  },
  {
    id: "sub-f-sulahan",
    sub: "F",
    title: "Manukaya ke Perbekel Desa Sulahan",
    declaredDistanceKm: 12.85,
    declaredDurationMinutes: 40,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 19.28,
    speedMode: "fixed_second",
    routeTextExcerpt: "SDN. 2 Penglumbaran - BR. Songlandak - SDN. 2 Sulahan - SMAN. 1 Susut.",
    status: "valid",
    notes: ["Sub F memiliki mode tetap detik dengan jarak eksplisit."]
  },
  {
    id: "sub-g-bangli-finish",
    sub: "G",
    title: "Sulahan ke finish Kantor Bupati Bangli",
    declaredDistanceKm: 6.02,
    declaredDurationMinutes: 10,
    distanceCountedInTotal: true,
    calculatedSpeedKmh: 36.12,
    speedMode: "remaining_distance",
    routeTextExcerpt: "BKN di LR, Jl. Brigjen Ngurah Rai - Kantor Bupati Bangli di kanan.",
    status: "valid",
    notes: ["Sisa jarak menuju finish dan dilanjutkan istirahat 60 menit."]
  }
];

const routeSeeds: RouteSeed[] = [
  {
    id: "sub-a-zero-trip",
    startLabel: "INNA Bali Heritage Hotel",
    finishLabel: "BR. Tangguntiti Tonja",
    waypointCount: 5,
    mapStatus: "needs_review",
    geometry: [
      { lat: -8.6563, lng: 115.2162 },
      { lat: -8.6468, lng: 115.2182 },
      { lat: -8.6352, lng: 115.2205 },
      { lat: -8.6202, lng: 115.2219 }
    ],
    routeSummary: "Jalur awal hasil OCR perlu validasi karena jarak sub A tidak tertulis eksplisit."
  },
  {
    id: "sub-b-penarungan",
    startLabel: "BR. Tangguntiti Tonja",
    finishLabel: "X Penarungan",
    waypointCount: 7,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.6202, lng: 115.2219 },
      { lat: -8.6001, lng: 115.224 },
      { lat: -8.5738, lng: 115.2286 },
      { lat: -8.5383, lng: 115.2264 }
    ],
    routeSummary: "Rute probabilitas utama mengikuti Darmasaba menuju Penarungan."
  },
  {
    id: "sub-c-bongkasa",
    startLabel: "X Penarungan",
    finishLabel: "BR. Tohpati",
    waypointCount: 18,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.5383, lng: 115.2264 },
      { lat: -8.511, lng: 115.2114 },
      { lat: -8.4802, lng: 115.2031 },
      { lat: -8.4465, lng: 115.2358 },
      { lat: -8.4302, lng: 115.2625 }
    ],
    routeSummary: "Sub C melewati koridor Baha, Sangeh, Bongkasa, lalu Tohpati."
  },
  {
    id: "sub-d-kedewatan",
    startLabel: "BR. Tohpati",
    finishLabel: "Perbekel Melinggih Kelod",
    waypointCount: 6,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.4302, lng: 115.2625 },
      { lat: -8.465, lng: 115.2709 },
      { lat: -8.4928, lng: 115.2696 },
      { lat: -8.5056, lng: 115.252 }
    ],
    routeSummary: "Sub D adalah segmen santai menuju area Kedewatan/Melinggih."
  },
  {
    id: "sub-e-manukaya",
    startLabel: "Perbekel Melinggih Kelod",
    finishLabel: "SDN 4 Manukaya",
    waypointCount: 14,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.5056, lng: 115.252 },
      { lat: -8.4662, lng: 115.2826 },
      { lat: -8.432, lng: 115.288 },
      { lat: -8.4062, lng: 115.3004 }
    ],
    routeSummary: "Sub E bergerak ke koridor Tegallalang, Sebatu, lalu Manukaya."
  },
  {
    id: "sub-f-sulahan",
    startLabel: "SDN 4 Manukaya",
    finishLabel: "Perbekel Desa Sulahan",
    waypointCount: 6,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.4062, lng: 115.3004 },
      { lat: -8.4136, lng: 115.341 },
      { lat: -8.4292, lng: 115.3657 },
      { lat: -8.4525, lng: 115.3761 }
    ],
    routeSummary: "Sub F melewati Penglumbaran, Songlandak, dan Sulahan."
  },
  {
    id: "sub-g-bangli-finish",
    startLabel: "Perbekel Desa Sulahan",
    finishLabel: "Kantor Bupati Bangli",
    waypointCount: 3,
    mapStatus: "mapped",
    geometry: [
      { lat: -8.4525, lng: 115.3761 },
      { lat: -8.4558, lng: 115.3964 },
      { lat: -8.4569, lng: 115.3558 }
    ],
    routeSummary: "Sub G adalah sisa jarak menuju finish di sekitar Bangli."
  }
];

const demoProbabilityOptions: ProbabilityRouteOption[] = [
  {
    id: "candidate-route-1",
    label: "Simpang utama dekat SDN",
    missingWaypointLabel: "X LR",
    confidence: 0.88,
    distanceDeviationPercent: 1.2,
    timeDeviationSeconds: 18,
    routeCorridorFit: 0.91,
    landmarkFit: 0.86,
    turnGeometryFit: 0.84,
    provider: "valhalla+local-poi",
    status: "recommended",
    reasons: [
      "Jarak A-B-C masuk toleransi sub-trayek",
      "Tipe simpang empat cocok dengan X LR",
      "Belokan BKR valid dari geometri jalan"
    ]
  },
  {
    id: "candidate-route-2",
    label: "Simpang pasar alternatif",
    missingWaypointLabel: "X LR",
    confidence: 0.73,
    distanceDeviationPercent: 3.8,
    timeDeviationSeconds: 54,
    routeCorridorFit: 0.74,
    landmarkFit: 0.8,
    turnGeometryFit: 0.69,
    provider: "osrm+osm",
    status: "review",
    reasons: [
      "Masih dalam koridor A-C",
      "Deviasi jarak melewati target championship",
      "Perlu konfirmasi visual atau survey"
    ]
  }
];

const uploadedBaliQuestionText = `Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024.
Trayek 1. Total jarak Trayek 1: 93,40 km. Total waktu Trayek 1: 270 menit.
A. Start dari INNA BALI HERITAGE Hotel (Zero) - BKN, Jl. Patimura - BKR, Jl. Suli - BKN di O Jl. Nangka - BR. Tangguntiti Tonja. Rute ini dijalani dengan santai selama 12 menit.
B. Rute dengan kec. tetap menit 19,67 km/jam selama 38 menit dan berakhir di X Penarungan. BR. Pengukuh - BR. Cabe - SD No. 1 Darmasaba - Jl. Carik Aban - BR. Blungbang.
C. Kec. tetap detik selama 75 menit sejauh 24,87 km. BR. Dajan Peken - Arah Baha/Mengwi - BR. Badung - BR. Ambengan - SDN. 1 Cau Belayu - arah Sangeh - BR. Tegal Gerana - BR. Tohpati.
D. Santai sambil melihat keindahan objek di Kedewatan selama 45 menit, kecepatan 15,64 km/jam. Arah Ubud/Gianyar - IJU - BR. Kedewatan - Perbekel Melinggih Kelod.
E. Dengan kecepatan rata-rata sejauh 21,9 km selama 50 menit dan berakhir di SDN. 4 Manukaya.
F. Berakhir di Perbekel Desa Sulahan dengan kecepatan tetap detik selama 40 menit, jarak 12,85 km.
G. Sisa jarak menuju finish sejauh 6,02 km selama 10 menit. BKN di LR, Jl. Brigjen Ngurah Rai - Kantor Bupati Bangli.`;

function buildTimingRows(masterStartTime: string): SubTrayekTimingRow[] {
  const startMinutes = parseClockMinutes(masterStartTime);
  let cumulativeMinutes = 0;

  return timingSeeds.map((seed) => {
    const cumulativeStartMinutes = cumulativeMinutes;
    const cumulativeFinishMinutes = cumulativeStartMinutes + seed.declaredDurationMinutes;
    cumulativeMinutes = cumulativeFinishMinutes;

    return {
      ...seed,
      kmPerSecond: kmPerSecond(seed.calculatedSpeedKmh),
      classificationLabel: classifySpeedMode(seed.speedMode),
      scheduledStartTime: formatClockFromMinutes(startMinutes + cumulativeStartMinutes),
      scheduledFinishTime: formatClockFromMinutes(startMinutes + cumulativeFinishMinutes),
      cumulativeStartMinutes,
      cumulativeFinishMinutes
    };
  });
}

function buildTimingValidation(masterStartTime: string): TrayekTimingValidation {
  return {
    trayekId: "pertamina-merah-putih-bali-2024-trayek-1",
    declaredDistanceKm: 93.4,
    declaredDurationMinutes: 270,
    calculatedDistanceKm: 93.4,
    calculatedDurationMinutes: 270,
    distanceDeltaKm: 0,
    durationDeltaMinutes: 0,
    toleranceDistanceKm: 0.05,
    toleranceDurationMinutes: 0,
    status: "warning",
    warnings: [
      "Sub A tidak mencantumkan jarak eksplisit; sistem mengisi jarak implisit 3,57 km dari selisih total.",
      "Header foto memiliki coretan tangan di atas total jarak. Navigator harus memilih angka resmi sebelum export final."
    ],
    rows: buildTimingRows(masterStartTime)
  };
}

function buildMappedRoutes(masterStartTime: string, roadbookReadyIds = new Set<string>()): MappedSubTrayekRoute[] {
  const timingRows = buildTimingRows(masterStartTime);
  return routeSeeds.map((routeSeed) => {
    const timingRow = timingRows.find((row) => row.id === routeSeed.id);
    if (!timingRow) {
      throw new Error(`Missing timing row for ${routeSeed.id}`);
    }

    return {
      ...routeSeed,
      sub: timingRow.sub,
      title: timingRow.title,
      distanceKm: timingRow.declaredDistanceKm ?? timingRow.inferredDistanceKm ?? null,
      durationMinutes: timingRow.declaredDurationMinutes,
      speedKmh: timingRow.calculatedSpeedKmh,
      kmPerSecond: timingRow.kmPerSecond,
      speedMode: timingRow.speedMode,
      scheduledStartTime: timingRow.scheduledStartTime,
      scheduledFinishTime: timingRow.scheduledFinishTime,
      cumulativeStartMinutes: timingRow.cumulativeStartMinutes,
      cumulativeFinishMinutes: timingRow.cumulativeFinishMinutes,
      roadbookReady: roadbookReadyIds.has(routeSeed.id),
      mapStatus: roadbookReadyIds.has(routeSeed.id) ? "finished" : routeSeed.mapStatus
    };
  });
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

function buildScheduleState(masterStartTime: string, roadbookReadyIds = new Set<string>()) {
  const timingValidation = buildTimingValidation(masterStartTime);
  const mappedSubTrayeks = buildMappedRoutes(masterStartTime, roadbookReadyIds);
  return {
    timingValidation,
    mappedSubTrayeks,
    execution: {
      activeSubTrayekId: mappedSubTrayeks[0]?.id ?? "sub-a-zero-trip",
      driverRunningSubTrayekId: mappedSubTrayeks[0]?.id,
      navigatorWorkingSubTrayekId: mappedSubTrayeks[1]?.id,
      masterStartTime,
      masterFinishTime: formatClockFromMinutes(parseClockMinutes(masterStartTime) + timingValidation.declaredDurationMinutes),
      totalDurationMinutes: timingValidation.declaredDurationMinutes,
      transitionWarningSeconds: TRANSITION_WARNING_SECONDS,
      roadbookReady: mappedSubTrayeks.every((route) => route.roadbookReady)
    }
  };
}

const initialSchedule = buildScheduleState(DEFAULT_MASTER_START_TIME);

export const useRallyWorkspaceStore = create<WorkspaceState>((set) => ({
  eventName: "Pertamina Merah Putih Bali - Trayek 1",
  rawText: uploadedBaliQuestionText,
  waypoints: [],
  roadbook: [],
  validation: {
    distanceStatus: "warning",
    timeStatus: "compliant",
    chainingStatus: "warning",
    score: 82
  },
  ...initialSchedule,
  photoOcr: {
    status: "timing_validated",
    photos: [],
    eventName: "Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
    trayekName: "Trayek 1",
    location: "Bali",
    lastMessage: "Contoh foto soal sudah diparsing menjadi tabel sub-trayek, jadwal start, dan kandidat mapping.",
    detectedFields: {
      eventName: "Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
      trayekName: "Trayek 1",
      location: "Bali",
      totalDistanceKm: 93.4,
      totalTimeMinutes: 270,
      headerDistanceCorrectionKm: 98
    }
  },
  routeEditor: {
    mode: "inspect",
    snapToRoad: true,
    routeLocked: false,
    selectedSubTrayekId: "sub-a-zero-trip"
  },
  probabilityOptions: demoProbabilityOptions,
  selectedProbabilityOptionId: "candidate-route-1",
  setRawText: (rawText) => set({ rawText }),
  setEventName: (eventName) => set({ eventName }),
  setMasterStartTime: (masterStartTime) =>
    set((state) => {
      const roadbookReadyIds = new Set(
        state.mappedSubTrayeks.filter((route) => route.roadbookReady).map((route) => route.id)
      );
      const scheduleState = buildScheduleState(masterStartTime, roadbookReadyIds);
      const roadbook = buildRoadbookFromRoutes(scheduleState.mappedSubTrayeks);
      return {
        ...scheduleState,
        roadbook,
        routeEditor: {
          ...state.routeEditor,
          selectedSubTrayekId: scheduleState.execution.activeSubTrayekId
        }
      };
    }),
  processQuestionPhotos: (photos) =>
    set((state) => {
      const scheduleState = buildScheduleState(state.execution.masterStartTime);
      return {
        eventName: "Pertamina Merah Putih Bali - Trayek 1",
        rawText: uploadedBaliQuestionText,
        ...scheduleState,
        roadbook: [],
        photoOcr: {
          status: "mapping_subtrayek",
          photos: photos.map((photo, index) => ({
            id: `photo-${index + 1}`,
            fileName: photo.fileName,
            previewUrl: photo.previewUrl,
            pageRole: index === 0 ? "subtrayek_a_d" : index === 1 ? "subtrayek_e_g" : "unknown",
            ocrConfidence: index < 2 ? 0.86 : 0.58,
            status: "parsed"
          })),
          eventName: "Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
          trayekName: "Trayek 1",
          location: "Bali",
          lastMessage: "Foto diterima, OCR demo mengisi tabel, jadwal, dan mapping sub-trayek untuk review navigator.",
          detectedFields: {
            eventName: "Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
            trayekName: "Trayek 1",
            location: "Bali",
            totalDistanceKm: 93.4,
            totalTimeMinutes: 270,
            headerDistanceCorrectionKm: 98
          }
        },
        routeEditor: {
          mode: "inspect",
          snapToRoad: true,
          routeLocked: false,
          selectedSubTrayekId: scheduleState.execution.activeSubTrayekId
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
  finishActiveSubTrayek: () =>
    set((state) => {
      const activeIndex = state.mappedSubTrayeks.findIndex(
        (route) => route.id === state.execution.activeSubTrayekId
      );
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
      const roadbookReady = mappedSubTrayeksNext.every((route) => route.roadbookReady);

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
