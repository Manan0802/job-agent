import { useEffect, useState } from "react";
import {
  BriefcaseIcon,
  ChatCircleTextIcon,
  KanbanIcon,
  MoonIcon,
  SunIcon,
  TargetIcon,
  UsersThreeIcon,
} from "@phosphor-icons/react";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { cn } from "@/lib/cn";
import { Loading } from "@/components/ui";
import { Today } from "@/views/Today";
import { Jobs } from "@/views/Jobs";
import { Referrals } from "@/views/Referrals";
import { Outreach } from "@/views/Outreach";
import { Pipeline } from "@/views/Pipeline";
import { ResumeGate } from "@/views/ResumeGate";

const VIEWS = [
  { id: "today", label: "Today", Icon: TargetIcon, View: Today },
  { id: "jobs", label: "Jobs", Icon: BriefcaseIcon, View: Jobs },
  { id: "referrals", label: "Referrals", Icon: UsersThreeIcon, View: Referrals },
  { id: "outreach", label: "Outreach", Icon: ChatCircleTextIcon, View: Outreach },
  { id: "pipeline", label: "Pipeline", Icon: KanbanIcon, View: Pipeline },
] as const;

type ViewId = (typeof VIEWS)[number]["id"];

const IDS = VIEWS.map((v) => v.id) as readonly string[];

/** Keep the view in the URL so a refresh stays put, links are shareable, and
    the browser's back button does what it looks like it should. */
function useView() {
  const read = () => {
    const id = window.location.hash.replace("#", "");
    return (IDS.includes(id) ? id : "today") as ViewId;
  };

  const [view, setView] = useState<ViewId>(read);

  useEffect(() => {
    const sync = () => setView(read());
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return [view, (next: ViewId) => { window.location.hash = next; }] as const;
}

function useTheme() {
  const [dark, setDark] = useState(
    () =>
      localStorage.getItem("theme") === "dark" ||
      (!localStorage.getItem("theme") &&
        window.matchMedia("(prefers-color-scheme: dark)").matches),
  );

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return { dark, toggle: () => setDark((d) => !d) };
}

export default function App() {
  const [view, setView] = useView();
  const { dark, toggle } = useTheme();
  // Everything downstream reads the profile, so this is the app's entry gate.
  const profile = useAsync(() => api.getProfile(), []);

  const Active = VIEWS.find((v) => v.id === view)!.View;

  return (
    <div className="min-h-[100dvh]">
      <header className="sticky top-0 z-10 border-b bg-canvas/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4">
          <span className="mr-2 font-semibold tracking-tight">Career Agent</span>

          <nav className="flex items-center gap-0.5 overflow-x-auto" aria-label="Sections">
            {VIEWS.map(({ id, label, Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setView(id)}
                aria-current={view === id ? "page" : undefined}
                className={cn(
                  "flex h-9 items-center gap-1.5 rounded-md px-2.5 text-sm font-medium whitespace-nowrap transition-colors",
                  view === id
                    ? "bg-accent-soft text-accent-ink"
                    : "text-ink-soft hover:bg-sunken hover:text-ink",
                )}
              >
                <Icon size={16} weight={view === id ? "fill" : "regular"} />
                {label}
              </button>
            ))}
          </nav>

          <button
            type="button"
            onClick={toggle}
            title={dark ? "Switch to light" : "Switch to dark"}
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            className="ml-auto flex h-9 w-9 items-center justify-center rounded-md text-ink-soft hover:bg-sunken hover:text-ink"
          >
            {dark ? <SunIcon size={17} /> : <MoonIcon size={17} />}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {profile.loading ? (
          <Loading rows={4} />
        ) : profile.data ? (
          <Active profile={profile.data} onGoTo={setView} />
        ) : (
          <ResumeGate onLoaded={profile.reload} />
        )}
      </main>
    </div>
  );
}
