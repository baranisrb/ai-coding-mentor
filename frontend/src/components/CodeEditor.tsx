import Editor from "@monaco-editor/react";
import type { Language } from "../types";

const MONACO_LANGUAGE_MAP: Record<Language, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  java: "java",
  cpp: "cpp",
  c: "c",
};

interface CodeEditorProps {
  code: string;
  language: Language;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string;
}

export default function CodeEditor({ code, language, onChange, readOnly = false, height = "360px" }: CodeEditorProps) {
  return (
    <div className="editor-shell">
      <Editor
        height={height}
        language={MONACO_LANGUAGE_MAP[language]}
        value={code}
        theme="vs-dark"
        onChange={(value) => onChange(value ?? "")}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          wordWrap: "on",
          padding: { top: 12 },
        }}
      />
    </div>
  );
}
