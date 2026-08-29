import type { TreatmentSubmission } from "../api/types";

export type TreatmentActionState =
  | { status: "idle"; message: null; submission: null }
  | { status: "error"; message: string; submission: null }
  | { status: "success"; message: string; submission: TreatmentSubmission };

export const initialTreatmentActionState: TreatmentActionState = {
  status: "idle",
  message: null,
  submission: null,
};
