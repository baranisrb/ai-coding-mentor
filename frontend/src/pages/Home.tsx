import { useState } from "react";
import CodeEditor from "../components/CodeEditor";
import LanguageSelector from "../components/LanguageSelector";
import DifficultySelector from "../components/DifficultySelector";
import ResultsDashboard from "../components/ResultsDashboard";
import Loader from "../components/Loader";
import ErrorBanner from "../components/ErrorBanner";
import { useAnalyze } from "../hooks/useAnalyze";
import type { Difficulty, Language } from "../types";

const DEFAULT_CODE = `def calculate_average(numbers):
    return sum(numbers) / len(numbers)
`;

export default function Home() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [language, setLanguage] = useState<Language>("python");
  const [difficulty, setDifficulty] = useState<Difficulty>("beginner");
  const [question, setQuestion] = useState("");

  const { loading, hintLoading, error, result, hint, runAnalysis, requestHint, reset } = useAnalyze();

  const handleAnalyze = () => {
    runAnalysis({ code, language, difficulty, question: question || undefined });
  };

  const handleHint = () => {
    requestHint({ code, language, difficulty });
  };

  const handleReset = () => {
    setCode(DEFAULT_CODE);
    setQuestion("");
    reset();
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>🧑‍🏫 AI Coding Mentor</h1>
        <p>Paste your code, and get bug analysis, fixes, tests, and mentorship — powered by Gemini.</p>
      </header>

      <main className="app-main">
        <section className="panel input-panel">
          <div className="controls-row">
            <LanguageSelector value={language} onChange={setLanguage} />
            <DifficultySelector value={difficulty} onChange={setDifficulty} />
          </div>

          <CodeEditor code={code} language={language} onChange={setCode} />

          <label className="field">
            <span className="field-label">Optional question for the mentor</span>
            <input
              type="text"
              placeholder="e.g. Why is this slow for large inputs?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </label>

          <div className="actions-row">
            <button className="primary-button" onClick={handleAnalyze} disabled={loading}>
              {loading ? "Analyzing…" : "Analyze Code"}
            </button>
            <button className="secondary-button" onClick={handleHint} disabled={hintLoading}>
              {hintLoading ? "Thinking…" : "Give Me a Hint"}
            </button>
            <button className="ghost-button" onClick={handleReset}>
              Reset
            </button>
          </div>

          {hint && (
            <div className="hint-box">
              💡 <strong>Hint:</strong> {hint}
            </div>
          )}
        </section>

        {error && <ErrorBanner message={error} />}
        {loading && <Loader />}
        {result && !loading && <ResultsDashboard result={result} language={language} />}
      </main>

      <footer className="app-footer">
        <span>AI Coding Mentor Agent — powered by the Google Gemini free tier.</span>
      </footer>
    </div>
  );
}
