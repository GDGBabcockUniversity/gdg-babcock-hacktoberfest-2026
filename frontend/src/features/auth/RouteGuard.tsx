import { useLayoutEffect, type ReactNode } from "react";
import { buildLoginPath, resolveAccess, type Access } from "./access";
import { ForbiddenPage } from "./ForbiddenPage";
import type { Session } from "./session";

interface RedirectProps {
  to: string;
  onRedirect: (to: string) => void;
}

function Redirect({ to, onRedirect }: RedirectProps) {
  useLayoutEffect(() => {
    onRedirect(to);
  }, [to, onRedirect]);

  return null;
}

function AccessPending() {
  return (
    <div className="access-pending container" role="status">
      <span className="access-spinner" aria-hidden="true" />
      <span className="sr-only">Checking your access</span>
    </div>
  );
}

interface RouteGuardProps {
  access: Access;
  session: Session;
  returnPath: string;
  onRequireLogin: (loginPath: string) => void;
  onBackToExams: () => void;
  children: ReactNode;
}

export function RouteGuard({
  access,
  session,
  returnPath,
  onRequireLogin,
  onBackToExams,
  children,
}: RouteGuardProps) {
  switch (resolveAccess(access, session)) {
    case "allow":
      return children;
    case "pending":
      return <AccessPending />;
    case "login":
      return <Redirect to={buildLoginPath(returnPath)} onRedirect={onRequireLogin} />;
    case "forbidden":
      return <ForbiddenPage onBackToExams={onBackToExams} />;
  }
}
