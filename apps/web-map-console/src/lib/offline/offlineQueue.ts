const QUEUE_STORAGE_KEY = "time-rally-offline-queue-v1";
const MAX_BODY_BYTES = 64 * 1024;
const MAX_ATTEMPTS = 5;

type QueuedRequest = {
  id: string;
  path: string;
  body: unknown;
  createdAt: string;
  attempts: number;
};

const QUEUEABLE_PATHS = new Set([
  "/v1/probability/route-edit",
  "/v1/tracking/ingest",
  "/v1/tracking/checkpoints/check"
]);

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readQueue(): QueuedRequest[] {
  if (!canUseStorage()) {
    return [];
  }
  const raw = window.localStorage.getItem(QUEUE_STORAGE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as QueuedRequest[]) : [];
  } catch {
    return [];
  }
}

function writeQueue(queue: QueuedRequest[]) {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
}

function bodySizeBytes(body: unknown) {
  return new Blob([JSON.stringify(body)]).size;
}

export function shouldQueueRequest(path: string, body: unknown) {
  return QUEUEABLE_PATHS.has(path) && bodySizeBytes(body) <= MAX_BODY_BYTES;
}

export function enqueueRequest(path: string, body: unknown) {
  const queue = readQueue();
  queue.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    path,
    body,
    createdAt: new Date().toISOString(),
    attempts: 0
  });
  writeQueue(queue);
}

export async function flushOfflineQueue(apiBaseUrl = "") {
  const queue = readQueue();
  if (!queue.length || (typeof navigator !== "undefined" && navigator.onLine === false)) {
    return { flushed: 0, remaining: queue.length };
  }

  const remaining: QueuedRequest[] = [];
  let flushed = 0;
  for (const item of queue) {
    try {
      const response = await fetch(`${apiBaseUrl}${item.path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(item.body)
      });
      if (response.ok) {
        flushed += 1;
        continue;
      }
    } catch {
      // Keep the queue intact for the next online event.
    }

    const attempts = item.attempts + 1;
    if (attempts < MAX_ATTEMPTS) {
      remaining.push({ ...item, attempts });
    }
  }

  writeQueue(remaining);
  return { flushed, remaining: remaining.length };
}
