import { Arrow } from "../../components/Arrow";

interface ForbiddenPageProps {
  onBackToExams: () => void;
}

export function ForbiddenPage({ onBackToExams }: ForbiddenPageProps) {
  return (
    <section className="forbidden-page container" aria-labelledby="forbidden-heading">
      <div className="exam-empty">
        <svg aria-hidden="true" viewBox="0 0 24 24" className="exam-empty-icon">
          <rect x="5" y="10.5" width="14" height="10" rx="2" />
          <path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3" />
        </svg>
        <h1 id="forbidden-heading" className="exam-empty-title">
          You don't have access to this page
        </h1>
        <p className="exam-empty-text">
          This page is for a different role. If you think you need it, ask an administrator.
        </p>
        <button type="button" className="button button-primary" onClick={onBackToExams}>
          Back to exams <Arrow />
        </button>
      </div>
    </section>
  );
}
