export type TransferActionState = {
  status: "idle" | "success" | "error";
  message: string;
};

export const initialTransferActionState: TransferActionState = { status: "idle", message: "" };
