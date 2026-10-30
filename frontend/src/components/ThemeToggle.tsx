import { useState } from "react";

type Theme = "light" | "dark";

const THEME_STORAGE_KEY = "gdg-ai-grader-theme";

function readStoredTheme(): Theme {
  try {
    return window.localStorage.getItem(THEME_STORAGE_KEY) === "dark"
      ? "dark"
      : "light";
  } catch {
    return "light";
  }
}

function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Theme switching remains available when browser storage is disabled.
  }
}

export function initializeTheme(): Theme {
  const theme = readStoredTheme();
  document.documentElement.dataset.theme = theme;
  return theme;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => initializeTheme());
  const nextTheme = theme === "dark" ? "light" : "dark";

  function toggleTheme() {
    applyTheme(nextTheme);
    setTheme(nextTheme);
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${nextTheme} mode`}
      aria-pressed={theme === "dark"}
    >
      {theme === "dark" ? (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
        </svg>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8 8.6 8.6 0 1 0 20.2 15.1Z" />
        </svg>
      )}
      <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}
