/**
 * CONTRATO CON EL BACKEND
 * Debe coincidir con api/app/schemas.py. Si cambias uno, cambia el otro.
 */
export type PublicState = "online" | "starting" | "stopping" | "offline" | "maintenance" | "unknown";

export interface ServerStatus {
  slug: string;
  state: PublicState;
  players: { current: number | null; max: number | null };
  version: string | null;
  checked_at: string | null; // fecha ISO
}

export interface StatusResponse {
  servers: ServerStatus[];
  generated_at: string;
}

/** Textos que ve el usuario para cada estado */
export const STATE_LABELS: Record<PublicState | "pending", string> = {
  online: "Online",
  starting: "Iniciando",
  stopping: "Deteniéndose",
  offline: "Offline",
  maintenance: "Mantenimiento",
  unknown: "Sin datos",
  pending: "Comprobando…",
};
