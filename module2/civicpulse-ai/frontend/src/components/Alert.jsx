// A short message box. Errors are announced by screen readers.
export default function Alert({ children }) {
  if (!children) return null;
  return (
    <p role="alert" className="rounded-lg border border-danger/30 bg-danger-soft px-4 py-3 text-danger">
      {children}
    </p>
  );
}
