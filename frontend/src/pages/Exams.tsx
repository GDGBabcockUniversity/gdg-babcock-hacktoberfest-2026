import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "../components/StateViews";
import { ExamCard } from "../features/exams/ExamCard";
import { ExamCardSkeleton } from "../features/exams/ExamCardSkeleton";
import { loadExams } from "../features/exams/mockExams";
import type { Exam } from "../features/exams/types";

const SKELETON_COUNT = 6;

type ExamsState =
  | { status: "loading" }
  | { status: "success"; exams: Exam[] }
  | { status: "error"; message: string };

function ExamListSkeleton() {
  return (
    <LoadingState message="Loading exams">
      <ul className="exam-grid" aria-hidden="true">
        {Array.from({ length: SKELETON_COUNT }, (_, index) => (
          <li key={index}>
            <ExamCardSkeleton />
          </li>
        ))}
      </ul>
    </LoadingState>
  );
}

export function ExamsPage() {
  const [retryCount, setRetryCount] = useState(0);
  const [state, setState] = useState<ExamsState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    loadExams()
      .then((exams) => {
        if (active) setState({ status: "success", exams });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "An unexpected error occurred. Please try again.",
        });
      });

    return () => {
      active = false;
    };
  }, [retryCount]);

  function retryLoadingExams() {
    setState({ status: "loading" });
    setRetryCount((count) => count + 1);
  }

  return (
    <section className="exams-page container" aria-labelledby="exams-heading">
      <header className="exams-header">
        <p className="eyebrow">
          <span className="eyebrow-line" /> EXAMS
        </p>
        <h1 id="exams-heading" className="exams-title">
          Your exams
        </h1>
        <p className="exams-subtitle">
          Every exam in your workspace, with its status and time limit.
        </p>
      </header>

      {state.status === "loading" && <ExamListSkeleton />}
      {state.status === "error" && (
        <ErrorState message={state.message} onRetry={retryLoadingExams} />
      )}
      {state.status === "success" && state.exams.length === 0 && (
        <EmptyState
          title="No exams yet"
          description="Exams appear here once an administrator creates them."
        />
      )}
      {state.status === "success" && state.exams.length > 0 && (
        <ul className="exam-grid" aria-label="Exams">
          {state.exams.map((exam) => (
            <li key={exam.id}>
              <ExamCard exam={exam} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
