import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-md text-center">
      <h1 className="mb-2 text-3xl font-semibold">Page not found</h1>
      <p className="mb-6 text-muted">The page you are looking for does not exist.</p>
      <Link to="/" className="btn btn-primary">
        Go to the home page
      </Link>
    </div>
  );
}
