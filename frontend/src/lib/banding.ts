// Heatmap colour banding (Req 3.2, Property 7)
export type Band = "green" | "amber" | "red";

export function band(score: number): Band {
  if (score <= 33) return "green";
  if (score <= 66) return "amber";
  return "red";
}

export const BAND_CLASSES: Record<Band, string> = {
  green: "bg-green-100 text-green-800 border-green-300",
  amber: "bg-amber-100 text-amber-800 border-amber-300",
  red: "bg-red-100 text-red-800 border-red-300",
};

export const BAND_BAR_CLASSES: Record<Band, string> = {
  green: "bg-green-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};
