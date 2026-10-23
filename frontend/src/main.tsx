/// <reference types="vite/client" />
import { Suspense, startTransition, use, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
import { clearStoredToken } from "./api";
import { Arrow } from "./components/Arrow";
import { canAccess, safeNextPath } from "./features/auth/access";
import { RouteGuard } from "./features/auth/RouteGuard";
import { ROUTES, findRoute } from "./features/auth/routes";
import { loadSession, type Session } from "./features/auth/session";

const LOADING_SESSION: Session = { status: "loading" };
const SIGN_IN_NOTICE = "Sign in to continue.";

interface AppLocation {
  pathname: string;
  search: string;
}

function readLocation(): AppLocation {
  return { pathname: window.location.pathname, search: window.location.search };
}

interface NavActionsProps {
  session: Session;
  pathname: string;
  navigate: (path: string) => void;
  onLogout: () => void;
}

function NavActions({ session, pathname, navigate, onLogout }: NavActionsProps) {
  if (session.status === "loading") {
    return <div className="nav-links nav-links-pending" />;
  }

  if (session.status === "anonymous") {
    return (
      <div className="nav-links">
        <button
          type="button"
          className="nav-button"
          onClick={() => navigate("/login")}
        >
          Open workspace <Arrow />
        </button>
      </div>
    );
  }

  return (
    <div className="nav-links">
      {ROUTES.filter((route) => route.navLabel && canAccess(route.access, session)).map(
        (route) => (
          <button
            key={route.path}
            type="button"
            className="nav-text-button"
            onClick={() => navigate(route.path)}
            aria-current={route.path === pathname ? "page" : undefined}
          >
            {route.navLabel}
          </button>
        ),
      )}
      <span style={{ fontSize: "13px", color: "#24754c", fontWeight: 600 }}>
        {session.user.email}
      </span>
      <button
        type="button"
        className="nav-button"
        onClick={onLogout}
      >
        Sign out
      </button>
    </div>
  );
}

interface AppShellProps {
  session: Session;
  location: AppLocation;
  noticeMessage: string | null;
  navigate: (path: string, notice?: string) => void;
  replace: (path: string, notice: string) => void;
  onLoginSuccess: () => void;
  onLogout: () => void;
}

function AppShell({
  session,
  location,
  noticeMessage,
  navigate,
  replace,
  onLoginSuccess,
  onLogout,
}: AppShellProps) {
  const route = findRoute(location.pathname);

  return (
    <main className="page-shell">
      <nav className="nav container" aria-label="Main navigation">
        <button
          type="button"
          className="brand"
          onClick={() => navigate("/")}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
          aria-label="GDG AI Grader home"
        >
          <span className="brand-mark">G</span>
          <span>GDG <em>AI</em> Grader</span>
        </button>

        <NavActions
          session={session}
          pathname={location.pathname}
          navigate={navigate}
          onLogout={onLogout}
        />
      </nav>

      <RouteGuard
        access={route.access}
        session={session}
        returnPath={location.pathname + location.search}
        onRequireLogin={(loginPath) => replace(loginPath, SIGN_IN_NOTICE)}
        onBackToExams={() => navigate("/exams")}
      >
        {route.render({ session, noticeMessage, navigate, onLoginSuccess })}
      </RouteGuard>
    </main>
  );
}

type ResolvedAppShellProps = Omit<AppShellProps, "session"> & {
  sessionPromise: Promise<Session>;
};

function ResolvedAppShell({ sessionPromise, ...shellProps }: ResolvedAppShellProps) {
  return <AppShell session={use(sessionPromise)} {...shellProps} />;
}

function App() {
  const [location, setLocation] = useState(readLocation);
  const [noticeMessage, setNoticeMessage] = useState<string | null>(null);
  const [sessionPromise, setSessionPromise] = useState(loadSession);

  useEffect(() => {
    const handlePopState = () => setLocation(readLocation());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function showCurrentLocation(notice?: string) {
    setLocation(readLocation());
    setNoticeMessage(notice || null);
  }

  function navigate(path: string, notice?: string) {
    window.history.pushState({}, "", path);
    showCurrentLocation(notice);
  }

  // Replacing the guarded URL keeps it out of history, so Back doesn't bounce
  // straight into the same login redirect again.
  function replace(path: string, notice: string) {
    window.history.replaceState({}, "", path);
    showCurrentLocation(notice);
  }

  function handleLoginSuccess() {
    const next = safeNextPath(new URLSearchParams(location.search).get("next"));
    startTransition(() => {
      setSessionPromise(loadSession());
      navigate(next ?? "/");
    });
  }

  function handleLogout() {
    clearStoredToken();
    startTransition(() => {
      setSessionPromise(Promise.resolve<Session>({ status: "anonymous" }));
      navigate("/");
    });
  }

  const shellProps = {
    location,
    noticeMessage,
    navigate,
    replace,
    onLoginSuccess: handleLoginSuccess,
    onLogout: handleLogout,
  };

  return (
    <Suspense fallback={<AppShell session={LOADING_SESSION} {...shellProps} />}>
      <ResolvedAppShell sessionPromise={sessionPromise} {...shellProps} />
    </Suspense>
  );
}

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(<App />);
