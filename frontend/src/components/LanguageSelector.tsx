import type { Language } from "../types";

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "python", label: "Python" },
  { value: "javascript", label: "JavaScript" },
  { value: "typescript", label: "TypeScript" },
  { value: "java", label: "Java" },
  { value: "cpp", label: "C++" },
  { value: "c", label: "C" },
];

interface Props {
  value: Language;
  onChange: (value: Language) => void;
}

export default function LanguageSelector({ value, onChange }: Props) {
  return (
    <label className="field">
      <span className="field-label">Language</span>
      <select value={value} onChange={(e) => onChange(e.target.value as Language)}>
        {LANGUAGES.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </label>
  );
}
