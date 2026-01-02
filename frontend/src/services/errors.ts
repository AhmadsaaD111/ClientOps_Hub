import axios from "axios";

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as any)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d?.msg).filter(Boolean).join("; ");
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong.";
}
