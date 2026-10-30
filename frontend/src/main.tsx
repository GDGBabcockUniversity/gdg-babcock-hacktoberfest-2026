import {
  Suspense,
  startTransition,
  use,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
} from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
import { Arrow } from "./components/Arrow";
import { initializeTheme, ThemeToggle } from "./components/ThemeToggle";
import { buildLoginPath, canAccess, safeNextPath } from "./features/auth/access";
import { RouteGuard } from "./features/auth/RouteGuard";
import { ROUTES, findRoute } from "./features/auth/routes";
import { loadSession, type Session } from "./features/auth/session";
import { onUnauthorized } from "./lib/http";
import { clearAccessToken } from "./lib/tokenStorage";

const LOADING_SESSION: Session = { status: "loading" };
const ANONYMOUS_SESSION: Session = { status: "anonymous" };
const SIGN_IN_NOTICE = "Sign in to continue.";
const SESSION_EXPIRED_NOTICE = "Your session has expired. Please sign in again.";


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
  const [menuOpen, setMenuOpen] = useState(false);
  const menuToggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  function handleNavigation(event: MouseEvent<HTMLAnchorElement>, path: string) {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    event.preventDefault();
    navigate(path);
    setMenuOpen(false);
  }

  function handleMenuKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape" && menuOpen) {
      setMenuOpen(false);
      menuToggleRef.current?.focus();
    }
  }

  if (session.status === "loading") {
    return renderNavigation(
      <span className="nav-links-pending" aria-label="Loading navigation" />,
    );
  }

  if (session.status === "anonymous") {
    return renderNavigation(
      <a
        className="nav-button"
        href="/login"
        onClick={(event) => handleNavigation(event, "/login")}
      >
        Open workspace <Arrow />
      </a>,
    );
  }

  return renderNavigation(
    <>
      {ROUTES.filter((route) => route.navLabel && canAccess(route.access, session)).map(
        (route) => (
          <a
            key={route.path}
            className="nav-text-link"
            href={route.path}
            onClick={(event) => handleNavigation(event, route.path)}
            aria-current={route.path === pathname ? "page" : undefined}
          >
            {route.navLabel}
          </a>
        ),
      )}
      <span className="nav-user-email">{session.user.email}</span>
      <button type="button" className="nav-button" onClick={onLogout}>
        Sign out
      </button>
    </>,
  );

  function renderNavigation(children: ReactNode) {
    return (
      <>
        <button
          ref={menuToggleRef}
          type="button"
          className="nav-menu-toggle"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <svg aria-hidden="true" viewBox="0 0 24 24">
            {menuOpen ? (
              <path d="m6 6 12 12M18 6 6 18" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
        <nav
          id="primary-navigation"
          className={`nav-links${menuOpen ? " nav-links-open" : ""}`}
          aria-label="Main navigation"
          onKeyDown={handleMenuKeyDown}
        >
          {children}
        </nav>
      </>
    );
  }
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
    <div className="page-shell">
      <header className="app-header">
        <div className="nav container">
          <a
            className="brand"
            href="/"
            onClick={(event) => {
              if (
                event.button !== 0 ||
                event.metaKey ||
                event.ctrlKey ||
                event.shiftKey ||
                event.altKey
              ) {
                return;
              }
              event.preventDefault();
              navigate("/");
            }}
            aria-label="GDG AI Grader home"
          >
            <span className="brand-mark">G</span>
            <span>GDG <em>AI</em> Grader</span>
          </a>

          <NavActions
            session={session}
            pathname={location.pathname}
            navigate={navigate}
            onLogout={onLogout}
          />
          <ThemeToggle />
        </div>
      </header>

      <main className="app-main">
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
    </div>
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

  useEffect(
    () =>
      onUnauthorized(() => {
        // Read the live URL: this listener is subscribed once, so `location` would be stale.
        const { pathname, search } = window.location;
        startTransition(() => {
          setSessionPromise(Promise.resolve(ANONYMOUS_SESSION));
          if (findRoute(pathname).access.kind !== "public") {
            replace(buildLoginPath(pathname + search), SESSION_EXPIRED_NOTICE);
          }
        });
      }),
    [],
  );

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
    clearAccessToken();
    startTransition(() => {
      setSessionPromise(Promise.resolve(ANONYMOUS_SESSION));
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

initializeTheme();

createRoot(rootElement).render(<App />);
