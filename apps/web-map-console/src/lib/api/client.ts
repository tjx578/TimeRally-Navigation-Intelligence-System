import {
  enqueueRequest,
  flushOfflineQueue,
  shouldQueueRequest
} from "../offline/offlineQueue";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function postJson<TRequest, TResponse>(
  path: string,
  body: TRequest
): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });
  } catch (error) {
    if (shouldQueueRequest(path, body)) {
      enqueueRequest(path, body);
      throw new Error(`Request queued offline for retry: ${path}`);
    }
    throw error;
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed ${response.status}: ${detail}`);
  }

  void flushOfflineQueue(API_BASE_URL);
  return response.json() as Promise<TResponse>;
}
