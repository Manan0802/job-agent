import { useState } from "react";
import { ArrowSquareOutIcon, MagnifyingGlassIcon, PlusIcon } from "@phosphor-icons/react";
import { api, ApiError, type Job } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill, SectionHeader } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { ViewProps } from "@/lib/view";

function scoreTone(score: number | null) {
  if (score === null) return "neutral" as const;
  if (score >= 75) return "good" as const;
  if (score >= 50) return "accent" as const;
  return "neutral" as const;
}

function JobCard({ job, onTrack }: { job: Job; onTrack: (job: Job) => void }) {
  const [tracked, setTracked] = useState(false);
  const reasons = job.llm_breakdown ? JSON.parse(job.llm_breakdown) : null;

  return (
    <Card className="px-4 py-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-medium">{job.title}</h3>
          <p className="mt-0.5 truncate text-sm text-ink-soft">
            {job.company}
            {job.location ? ` · ${job.location}` : ""}
          </p>
        </div>
        {job.llm_score !== null && (
          <span
            className={cn(
              "tabular shrink-0 rounded-md px-2 py-1 text-sm font-medium",
              scoreTone(job.llm_score) === "good" && "bg-good-soft text-good",
              scoreTone(job.llm_score) === "accent" && "bg-accent-soft text-accent-ink",
              scoreTone(job.llm_score) === "neutral" && "bg-sunken text-ink-soft",
            )}
          >
            {Math.round(job.llm_score)}
          </span>
        )}
      </div>

      {reasons?.reasoning && (
        <p className="mt-2 text-[13px] leading-relaxed text-ink-soft">{reasons.reasoning}</p>
      )}

      {!!reasons?.matched_skills?.length && (
        <div className="mt-2.5 flex flex-wrap gap-1">
          {reasons.matched_skills.slice(0, 5).map((skill: string) => (
            <Pill key={skill} tone="good">
              {skill}
            </Pill>
          ))}
          {reasons.missing_skills?.slice(0, 2).map((skill: string) => (
            <Pill key={skill} tone="attention">
              needs {skill}
            </Pill>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-2">
        <Button
          size="sm"
          variant={tracked ? "ghost" : "secondary"}
          disabled={tracked}
          onClick={() => {
            onTrack(job);
            setTracked(true);
          }}
        >
          {tracked ? "Tracking" : <><PlusIcon size={14} /> Track</>}
        </Button>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-[13px] font-medium text-ink-soft hover:bg-sunken hover:text-ink"
          >
            Open <ArrowSquareOutIcon size={14} />
          </a>
        )}
        {job.source_engine && (
          <span className="ml-auto text-[11px] text-ink-faint">{job.source_engine}</span>
        )}
      </div>
    </Card>
  );
}

export function Jobs({ profile }: ViewProps) {
  const saved = useAsync(() => api.listJobs(50), []);
  // The most recent job title beats a bare keyword: profile.keywords[0] was
  // "AI", which is too broad to return anything useful.
  const [term, setTerm] = useState(
    profile.experience?.find((e) => e.role)?.role ?? profile.keywords?.[0] ?? "software engineer",
  );
  const [location, setLocation] = useState(profile.personal.location ?? "India");
  const [hunting, setHunting] = useState(false);
  const [huntError, setHuntError] = useState<string | null>(null);
  const [huntNote, setHuntNote] = useState<string | null>(null);

  async function hunt() {
    setHunting(true);
    setHuntError(null);
    setHuntNote(null);
    try {
      const result = await api.huntJobs(term, location, 15);
      setHuntNote(
        `Scanned ${result.total_found} listings and scored the closest ${result.scored_count}.`,
      );
      saved.reload();
    } catch (e) {
      setHuntError(e instanceof ApiError ? e.message : "The hunt failed");
    } finally {
      setHunting(false);
    }
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Every board at once, ranked against your profile. Only the closest matches get read
          by the model, which is what keeps this free.
        </p>
      </div>

      <Card className="flex flex-wrap items-end gap-3 p-4">
        <label className="grid min-w-[190px] flex-1 gap-1.5">
          <span className="text-[13px] font-medium">Role</span>
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="AI engineer"
            className="h-9 rounded-md border bg-surface px-3 text-sm placeholder:text-ink-faint"
          />
        </label>
        <label className="grid min-w-[150px] flex-1 gap-1.5">
          <span className="text-[13px] font-medium">Location</span>
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="India"
            className="h-9 rounded-md border bg-surface px-3 text-sm placeholder:text-ink-faint"
          />
        </label>
        <Button variant="primary" onClick={hunt} disabled={hunting || !term.trim()}>
          <MagnifyingGlassIcon size={15} />
          {hunting ? "Hunting…" : "Hunt jobs"}
        </Button>
      </Card>

      {hunting && (
        <p className="text-sm text-ink-soft">
          Scraping every source, ranking locally, then scoring the shortlist. This takes a
          minute or two.
        </p>
      )}
      {huntNote && <p className="text-sm text-good">{huntNote}</p>}
      {huntError && <ErrorNote message={huntError} onRetry={hunt} />}

      <section>
        <SectionHeader title="Best matches" count={saved.data?.count} />
        {saved.loading ? (
          <Loading rows={3} />
        ) : saved.error ? (
          <ErrorNote message={saved.error} onRetry={saved.reload} />
        ) : saved.data?.jobs.length ? (
          <div className="grid gap-2">
            {saved.data.jobs.map((job) => (
              <JobCard key={job.id} job={job} onTrack={(j) => api.trackJob(j.id)} />
            ))}
          </div>
        ) : (
          <Empty
            title="No jobs yet"
            hint="Run a hunt and the closest matches to your profile will land here, scored and explained."
          />
        )}
      </section>
    </div>
  );
}
