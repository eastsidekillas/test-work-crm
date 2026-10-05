import { Injectable } from "@angular/core";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
function errorText(data: unknown): string {
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.map(errorText).join(" ");
  if (data && typeof data === "object")
    return Object.values(data).map(errorText).join(" ");
  return "Не удалось выполнить запрос.";
}
@Injectable({ providedIn: "root" })
export class ApiService {
  async request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (method !== "GET") {
      const cookie = document.cookie
        .split("; ")
        .find((v) => v.startsWith("csrftoken="));
      if (cookie)
        headers["X-CSRFToken"] = decodeURIComponent(
          cookie.slice("csrftoken=".length),
        );
    }
    let response: Response;
    try {
      response = await fetch("/api/" + path, {
        method,
        headers,
        credentials: "same-origin",
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new ApiError(
        0,
        "Нет связи с сервером. Проверьте подключение и повторите.",
      );
    }
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok)
      throw new ApiError(
        response.status,
        response.status === 403
          ? "Сессия завершилась. Войдите снова."
          : errorText(data),
      );
    return data as T;
  }
}
export function messageOf(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Не удалось выполнить действие.";
}
