import type { ReactNode } from "react";

interface LoadingStateProps {
  message: string;
  children?: ReactNode;
}

export function LoadingState({ message, children }: LoadingStateProps) {
  return (
    <div
      className="async-state async-state-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="state-spinner" aria-hidden="true" />
      <p className="async-state-message">{message}</p>
      {children}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="async-state async-state-empty">
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="async-state-icon"
      >
        <path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10A.5.5 0 0 1 7 20V3.5Z" />
        <path d="M14 3.5V8h4M10 12.5h5M10 16h3" />
      </svg>
      <h2 className="async-state-title">{title}</h2>
      <p className="async-state-description">{description}</p>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
  title?: string;
}

export function ErrorState({
  message,
  onRetry,
  title = "Unable to load this content",
}: ErrorStateProps) {
  return (
    <div className="async-state async-state-error" role="alert">
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="async-state-icon"
      >
        <path d="M12 3.5 22 20.5H2L12 3.5Z" />
        <path d="M12 9v5M12 17.5h.01" />
      </svg>
      <h2 className="async-state-title">{title}</h2>
      <p className="async-state-description">{message}</p>
      <button type="button" className="state-retry-button" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}
