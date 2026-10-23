import type { ReactNode } from "react";
import { AdminExamBuilderPage } from "../../pages/AdminExamBuilder";
import { ExamsPage } from "../../pages/Exams";
import { LandingPage } from "../../pages/Landing";
import { LoginPage } from "../../pages/Login";
import { RegisterPage } from "../../pages/Register";
import { ResultsPage } from "../../pages/Results";
import type { Access } from "./access";
import type { Session } from "./session";

export interface RouteContext {
  session: Session;
  noticeMessage: string | null;
  navigate: (path: string, notice?: string) => void;
  onLoginSuccess: () => void;
}

export interface AppRoute {
  path: string;
  access: Access;
  navLabel?: string;
  render: (context: RouteContext) => ReactNode;
}

const PUBLIC: Access = { kind: "public" };
const SIGNED_IN: Access = { kind: "authenticated" };
const EXAM_MANAGERS: Access = { kind: "roles", roles: ["admin", "superadmin"] };

const LANDING_ROUTE: AppRoute = {
  path: "/",
  access: PUBLIC,
  render: ({ session, navigate }) => (
    <LandingPage signedIn={session.status === "authenticated"} onNavigate={navigate} />
  ),
};

export const ROUTES: readonly AppRoute[] = [
  LANDING_ROUTE,
  {
    path: "/login",
    access: PUBLIC,
    render: ({ navigate, noticeMessage, onLoginSuccess }) => (
      <LoginPage
        onLoginSuccess={onLoginSuccess}
        onNavigateToRegister={() => navigate("/register")}
        onCancel={() => navigate("/")}
        noticeMessage={noticeMessage}
      />
    ),
  },
  {
    path: "/register",
    access: PUBLIC,
    render: ({ navigate }) => (
      <RegisterPage
        onRegisterSuccess={() =>
          navigate(
            "/login",
            "Account created successfully! Please sign in with your credentials."
          )
        }
        onNavigateToLogin={() => navigate("/login")}
        onCancel={() => navigate("/")}
      />
    ),
  },
  { path: "/exams", access: SIGNED_IN, navLabel: "Exams", render: () => <ExamsPage /> },
  { path: "/results", access: SIGNED_IN, navLabel: "Results", render: () => <ResultsPage /> },
  {
    path: "/admin/exams/new",
    access: EXAM_MANAGERS,
    navLabel: "New exam",
    render: () => <AdminExamBuilderPage />,
  },
];

export function findRoute(pathname: string): AppRoute {
  return ROUTES.find((route) => route.path === pathname) ?? LANDING_ROUTE;
}
