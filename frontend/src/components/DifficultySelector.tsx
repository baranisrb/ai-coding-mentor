import type { Difficulty } from "../types";

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

interface Props {
  value: Difficulty;
  onChange: (value: Difficulty) => void;
}

export default function DifficultySelector({ value, onChange }: Props) {
  return (
    <label className="field">
      <span className="field-label">Difficulty</span>
      <select value={value} onChange={(e) => onChange(e.target.value as Difficulty)}>
        {DIFFICULTIES.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
      </select>
    </label>
  );
}
