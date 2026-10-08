export type GradeItem = {
  code: string;
  name: string;
  value: number;
  unit: string;
  grade: number | null;
  grade_status: string | null;
  compliant: boolean;
  limit_value: number | null;
  exceed_ratio: number | null;
};

export type GradeResponse = {
  overall_grade: number | null;
  overall_label: string | null;
  grade_status: string | null;
  summary: string | null;
  deciding_factors: string[];
  unknown_indicators: string[];
  boundary_non_compliant: string[];
  error: string | null;
  items: Record<string, GradeItem>;
};

export const GRADE_COLORS: Record<number, string> = {
  1: "#2563eb",
  2: "#0891b2",
  3: "#16a34a",
  4: "#ca8a04",
  5: "#ea580c",
  6: "#dc2626",
};

export const METHOD_LEVELS: { value: number; label: string }[] = [
  { value: 1, label: "① 专业机构实验室检测" },
  { value: 2, label: "② 便携式仪器现场检测" },
  { value: 3, label: "③ 家用试剂快速检测" },
  { value: 4, label: "④ 感官/主观描述" },
];
