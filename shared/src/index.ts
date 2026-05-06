/** Shared API contracts (extension, dashboard, landing). */
export type HealthResponse = {
  status: "ok" | "degraded";
  db: "connected" | "disconnected";
  redis: "connected" | "disconnected";
};

export const API_VERSION = "v1" as const;
