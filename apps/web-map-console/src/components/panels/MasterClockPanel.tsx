import { AlarmClock, Clock3, Gauge, Hourglass, TimerReset } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

declare global {
  interface Window {
    time_is_widget?: {
      init: (config: Record<string, unknown>) => void;
    };
    __timeRallyTimeIsCallback?: (renderedTime: string) => void;
  }
}

function parseClockSeconds(value: string) {
  const [hours = "0", minutes = "0"] = value.split(":");
  return Number(hours) * 3600 + Number(minutes) * 60;
}

function parseTimeIsSeconds(value: string | null) {
  if (!value) {
    return null;
  }
  const match = value.match(/(\d{1,2}):(\d{2}):(\d{2})/);
  if (!match) {
    return null;
  }
  return Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]);
}

function formatClock(date: Date) {
  return date.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}

function formatDuration(totalSeconds: number) {
  const clamped = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(clamped / 60);
  const seconds = clamped % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function modeLabel(mode: string) {
  if (mode === "fixed_second") return "Tetap detik";
  if (mode === "average_speed") return "Rata-rata";
  if (mode === "remaining_distance") return "Sisa finish";
  return "Zero trip";
}

export function MasterClockPanel() {
  const routes = useRallyWorkspaceStore((state) => state.mappedSubTrayeks);
  const execution = useRallyWorkspaceStore((state) => state.execution);
  const setMasterStartTime = useRallyWorkspaceStore((state) => state.setMasterStartTime);
  const selectSubTrayekRoute = useRallyWorkspaceStore((state) => state.selectSubTrayekRoute);
  const [now, setNow] = useState(() => new Date());
  const [timeIsText, setTimeIsText] = useState<string | null>(null);
  const [timeAuthorityStatus, setTimeAuthorityStatus] = useState("Time.is connecting");

  useEffect(() => {
    const timerId = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timerId);
  }, []);

  useEffect(() => {
    window.__timeRallyTimeIsCallback = (renderedTime: string) => {
      setTimeIsText(renderedTime);
      setTimeAuthorityStatus("Time.is synced");
    };

    const initWidget = () => {
      window.time_is_widget?.init({
        Bali_z41b: {
          template: "TIME",
          time_format: "hours:minutes:seconds",
          callback: "__timeRallyTimeIsCallback"
        }
      });
    };

    if (window.time_is_widget) {
      initWidget();
      return;
    }

    const existingScript = document.querySelector<HTMLScriptElement>("script[data-time-rally-time-is]");
    if (existingScript) {
      existingScript.addEventListener("load", initWidget, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://widget.time.is/t.js";
    script.async = true;
    script.dataset.timeRallyTimeIs = "true";
    script.addEventListener("load", initWidget, { once: true });
    script.addEventListener("error", () => setTimeAuthorityStatus("Fallback device clock"), {
      once: true
    });
    document.body.appendChild(script);
  }, []);

  const clock = useMemo(() => {
    const timeIsSeconds = parseTimeIsSeconds(timeIsText);
    const nowSeconds = timeIsSeconds ?? now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
    const startSeconds = parseClockSeconds(execution.masterStartTime);
    const elapsedSeconds = Math.max(0, nowSeconds - startSeconds);
    const totalSeconds = execution.totalDurationMinutes * 60;
    const clampedElapsedSeconds = Math.min(elapsedSeconds, totalSeconds);
    const activeRoute =
      routes.find(
        (route) =>
          clampedElapsedSeconds >= route.cumulativeStartMinutes * 60 &&
          clampedElapsedSeconds < route.cumulativeFinishMinutes * 60
      ) ?? routes[routes.length - 1];

    const elapsedInSubSeconds = activeRoute
      ? Math.max(0, clampedElapsedSeconds - activeRoute.cumulativeStartMinutes * 60)
      : 0;
    const remainingInSubSeconds = activeRoute
      ? Math.max(0, activeRoute.cumulativeFinishMinutes * 60 - clampedElapsedSeconds)
      : 0;
    let targetDistanceKm: number | null = null;
    if (activeRoute?.kmPerSecond != null) {
      targetDistanceKm = Math.min(
        activeRoute.distanceKm ?? Number.POSITIVE_INFINITY,
        elapsedInSubSeconds * activeRoute.kmPerSecond
      );
    }

    return {
      activeRoute,
      clampedElapsedSeconds,
      elapsedInSubSeconds,
      remainingInSubSeconds,
      targetDistanceKm,
      warningActive:
        remainingInSubSeconds > 0 && remainingInSubSeconds <= execution.transitionWarningSeconds
    };
  }, [
    execution.masterStartTime,
    execution.totalDurationMinutes,
    execution.transitionWarningSeconds,
    now,
    routes,
    timeIsText
  ]);

  useEffect(() => {
    if (clock.activeRoute && clock.activeRoute.id !== execution.activeSubTrayekId) {
      selectSubTrayekRoute(clock.activeRoute.id);
    }
  }, [clock.activeRoute, execution.activeSubTrayekId, selectSubTrayekRoute]);

  const activeRoute = clock.activeRoute;

  return (
    <div className="panel-section master-clock-panel">
      <div className="panel-title-row">
        <h2 className="panel-heading">Jam Master</h2>
        <span className={clock.warningActive ? "status-pill timing-warning" : "status-pill timing-valid"}>
          {timeIsText ?? formatClock(now)}
        </span>
      </div>

      <div className="time-authority">
        <a href="https://time.is/Bali" id="time_is_link" rel="nofollow">
          Time.is Bali
        </a>
        <span id="Bali_z41b">{timeIsText ?? "--:--:--"}</span>
        <small>{timeAuthorityStatus}</small>
      </div>

      <label className="field-label" htmlFor="master-start-time">
        Start rally
      </label>
      <div className="time-input-row">
        <input
          id="master-start-time"
          type="time"
          value={execution.masterStartTime}
          onChange={(event) => setMasterStartTime(event.target.value)}
        />
        <span>Finish {execution.masterFinishTime}</span>
      </div>

      {activeRoute ? (
        <div className="master-clock-grid">
          <div className="master-clock-primary">
            <Clock3 size={18} />
            <div>
              <span>Sub aktif</span>
              <strong>{activeRoute.sub}</strong>
            </div>
          </div>
          <div className="master-clock-metric">
            <AlarmClock size={14} />
            <span>{activeRoute.scheduledStartTime} - {activeRoute.scheduledFinishTime}</span>
          </div>
          <div className="master-clock-metric">
            <Hourglass size={14} />
            <span>Sisa {formatDuration(clock.remainingInSubSeconds)}</span>
          </div>
          <div className="master-clock-metric">
            <Gauge size={14} />
            <span>{modeLabel(activeRoute.speedMode)} / {activeRoute.speedKmh?.toFixed(2) ?? "-"} km/jam</span>
          </div>
        </div>
      ) : null}

      {clock.warningActive && activeRoute ? (
        <div className="segment-warning">
          <TimerReset size={16} />
          <span>Pindah ke sub berikutnya dalam {formatDuration(clock.remainingInSubSeconds)}</span>
        </div>
      ) : null}

      {activeRoute?.speedMode === "fixed_second" ? (
        <div className="tap-detik-box">
          <span>Mode tetap detik</span>
          <strong>{activeRoute.kmPerSecond?.toFixed(6)} km/detik</strong>
          <div className="tap-distance">{clock.targetDistanceKm?.toFixed(3) ?? "0.000"} km</div>
          <p>Samakan odo mobil dengan jarak acuan ini sepanjang sub {activeRoute.sub}.</p>
        </div>
      ) : null}
    </div>
  );
}
