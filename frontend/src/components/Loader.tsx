interface Props {
  label?: string;
}

export default function Loader({ label = "Analyzing your code…" }: Props) {
  return (
    <div className="loader">
      <div className="spinner" />
      <span>{label}</span>
    </div>
  );
}
