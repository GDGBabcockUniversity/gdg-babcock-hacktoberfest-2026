import { Arrow } from "../components/Arrow";

interface LandingPageProps {
  signedIn: boolean;
  onNavigate: (path: string) => void;
}

export function LandingPage({ signedIn, onNavigate }: LandingPageProps) {
  return (
    <>
      <section className="hero hero-centered container" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-line" /> AI-ASSISTED GRADING</p>
          <h1>Clear feedback.<br /><span>Less busywork.</span></h1>
          <p className="hero-text">Review AI suggestions, adjust when needed, and share thoughtful feedback with every learner.</p>
          <div className="hero-actions">
            <button
              type="button"
              className="button button-primary"
              onClick={() => onNavigate(signedIn ? "/" : "/login")}
            >
              {signedIn ? "Go to workspace" : "Start grading"} <Arrow />
            </button>
          </div>
        </div>
      </section>

      <section className="proof-strip">
        <div className="container proof-inner">
          <p>HOW IT WORKS</p>
          <div className="proof-items"><span><b>1.</b> Upload</span><i /><span><b>2.</b> Review</span><i /><span><b>3.</b> Share feedback</span></div>
        </div>
      </section>
    </>
  );
}
