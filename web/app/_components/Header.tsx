import AuthStatus from "./AuthStatus";
import ThemeToggle from "./ThemeToggle";

export default function Header() {
  return (
    <header className="border-b border-[var(--border)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4 sm:px-8">
        <a
          href="/"
          className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]"
        >
          Board of Innovation
        </a>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <AuthStatus />
        </div>
      </div>
    </header>
  );
}
