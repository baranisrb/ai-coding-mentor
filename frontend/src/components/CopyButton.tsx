import { useState } from "react";

interface Props {
  text: string;
  label?: string;
}

export default function CopyButton({ text, label = "Copy" }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API can fail in some contexts; fail silently, non-critical.
    }
  };

  return (
    <button className="copy-button" onClick={handleCopy} type="button">
      {copied ? "Copied ✓" : label}
    </button>
  );
}
