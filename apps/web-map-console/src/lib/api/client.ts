const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function postJson<TRequest, TResponse>(
  path: string,
  body: TRequest
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed ${response.status}: ${detail}`);
  }

  return response.json() as Promise<TResponse>;
}

