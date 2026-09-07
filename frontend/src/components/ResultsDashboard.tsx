import type { AnalyzeResponse, Language } from "../types";
import ScoreGauge from "./ScoreGauge";
import BugCard from "./BugCard";
import CodeEditor from "./CodeEditor";
import CopyButton from "./CopyButton";

interface Props {
  result: AnalyzeResponse;
  language: Language;
}

export default function ResultsDashboard({ result, language }: Props) {
  const { mentor, static_analysis, disclaimer } = result;

  return (
    <div className="results-dashboard">
      {mentor.analysis_status === "partial" && (
        <div className="warning-banner">
          The AI response could not be fully validated this time. Showing what we have —
          feel free to click Analyze again.
        </div>
      )}

      <section className="panel">
        <h2>Code Quality Score</h2>
        <ScoreGauge score={mentor.code_quality_score} />
      </section>

      <section className="panel">
        <h2>Overview</h2>
        <p>{mentor.summary}</p>
        {!static_analysis.fully_supported && (
          <p className="note">
            Deterministic static analysis is not yet available for {static_analysis.language}; findings for
            this language come from AI analysis only.
          </p>
        )}
        {mentor.strengths.length > 0 && (
          <>
            <h3>What you did well</h3>
            <ul>
              {mentor.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="panel">
        <h2>Bugs ({mentor.bugs.length})</h2>
        {mentor.bugs.length === 0 ? (
          <p>No bugs found. Nice work!</p>
        ) : (
          <div className="bug-list">
            {mentor.bugs.map((bug, i) => (
              <BugCard key={i} bug={bug} index={i} />
            ))}
          </div>
        )}
      </section>

      {mentor.fixed_code && (
        <section className="panel">
          <div className="panel-header">
            <h2>Corrected Code</h2>
            <CopyButton text={mentor.fixed_code} />
          </div>
          <CodeEditor code={mentor.fixed_code} language={language} onChange={() => {}} readOnly height="280px" />
          {mentor.changes.length > 0 && (
            <>
              <h3>Changes made</h3>
              <ul>
                {mentor.changes.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      {mentor.tests && (
        <section className="panel">
          <div className="panel-header">
            <h2>Generated Tests</h2>
            <CopyButton text={mentor.tests} />
          </div>
          <CodeEditor code={mentor.tests} language={language} onChange={() => {}} readOnly height="240px" />
          {mentor.test_explanations.length > 0 && (
            <ul>
              {mentor.test_explanations.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          )}
        </section>
      )}

      {mentor.edge_cases.length > 0 && (
        <section className="panel">
          <h2>Edge Cases to Consider</h2>
          <ul>
            {mentor.edge_cases.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </section>
      )}

      {mentor.learning_points.length > 0 && (
        <section className="panel">
          <h2>What You Learned</h2>
          <ul>
            {mentor.learning_points.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </section>
      )}

      {mentor.next_exercise && (
        <section className="panel highlight-panel">
          <h2>Next Exercise</h2>
          <p>{mentor.next_exercise}</p>
        </section>
      )}

      <p className="disclaimer">{disclaimer}</p>
    </div>
  );
}
