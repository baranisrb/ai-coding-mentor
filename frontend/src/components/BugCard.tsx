import type { Bug } from "../types";

const SEVERITY_COLOR: Record<Bug["severity"], string> = {
  LOW: "#84cc16",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

const TYPE_ICON: Record<Bug["type"], string> = {
  syntax: "🔤",
  runtime: "💥",
  logic: "🧠",
  edge_case: "🧩",
  performance: "⚡",
  security: "🔒",
  quality: "🧹",
};

interface Props {
  bug: Bug;
  index: number;
}

export default function BugCard({ bug, index }: Props) {
  return (
    <div className="bug-card">
      <div className="bug-card-header">
        <span className="bug-icon">{TYPE_ICON[bug.type]}</span>
        <span className="bug-title">
          Bug {index + 1}: {bug.title}
        </span>
        <span className="severity-badge" style={{ backgroundColor: SEVERITY_COLOR[bug.severity] }}>
          {bug.severity}
        </span>
      </div>
      <div className="bug-meta">
        <span>Type: {bug.type.replace("_", " ")}</span>
        <span>Line: {bug.line ?? "unknown"}</span>
        <span className={bug.verified ? "verified-tag" : "ai-suggested-tag"}>
          {bug.verified ? "✔ Statically verified" : "✦ AI-suggested"}
        </span>
      </div>
      <p>
        <strong>Problem:</strong> {bug.problem}
      </p>
      <p>
        <strong>Why:</strong> {bug.explanation}
      </p>
      <p>
        <strong>Suggested fix:</strong> {bug.suggested_fix}
      </p>
    </div>
  );
}
