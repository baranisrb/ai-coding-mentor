interface Props {
  score: number;
}

function bandFor(score: number): { label: string; color: string } {
  if (score >= 85) return { label: "Excellent", color: "#22c55e" };
  if (score >= 65) return { label: "Good", color: "#84cc16" };
  if (score >= 45) return { label: "Needs work", color: "#eab308" };
  return { label: "Needs significant work", color: "#ef4444" };
}

export default function ScoreGauge({ score }: Props) {
  const band = bandFor(score);
  return (
    <div className="score-gauge">
      <div className="score-circle" style={{ borderColor: band.color }}>
        <span className="score-value">{score}</span>
        <span className="score-max">/100</span>
      </div>
      <div>
        <div className="score-band" style={{ color: band.color }}>
          {band.label}
        </div>
        <div className="score-note">AI-assisted estimate, not an absolute measurement.</div>
      </div>
    </div>
  );
}
