import { useState } from "react";
import { ArrowSquareOutIcon, CaretRightIcon, ChatCircleTextIcon } from "@phosphor-icons/react";
import { api, ApiError, type Application, type InterviewPrep } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill } from "@/components/ui";
import { InterviewPanel } from "@/components/InterviewPanel";
import type { ViewProps } from "@/lib/view";

/* The pipeline as the user thinks about it, not as the database stores it. */
const COLUMNS = [
  { id: "saved", label: "Saved" },
  { id: "applied", label: "Applied" },
  { id: "referral_pending", label: "Waiting on referral" },
  { id: "interview_scheduled", label: "Interview booked" },
  { id: "interview_done", label: "Interviewed" },
  { id: "offer_received", label: "Offer" },
] as const;

const NEXT_STAGE: Record<string, string> = {
  saved: "applied",
  applied: "interview_scheduled",
  referral_pending: "applied",
  interview_scheduled: "interview_done",
  interview_done: "offer_received",
  offer_received: "accepted",
};

/* Prep is offered only while an interview is still ahead. Offering it on every
   job you saved would burn the free tier on postings you never applied to, and
   offering it after the interview is advice that arrives too late. */
const INTERVIEW_AHEAD = new Set(["applied", "referral_pending", "interview_scheduled"]);

const NEXT_LABEL: Record<string, string> = {
  saved: "Mark applied",
  applied: "Got an interview",
  referral_pending: "Mark applied",
  interview_scheduled: "Interview done",
  interview_done: "Got an offer",
  offer_received: "Accept",
};

function ApplicationCard({
  application,
  onMove,
  onPrep,
  busy,
}: {
  application: Application;
  onMove: (id: string, status: string) => void;
  onPrep: (application: Application) => void;
  busy: boolean;
}) {
  const next = NEXT_STAGE[application.status];
  const canPrep = !!application.job_id && INTERVIEW_AHEAD.has(application.status);

  return (
    <Card className="min-w-0 px-3 py-2.5">
      <p className="truncate text-[13px] font-medium" title={application.role_title ?? ""}>
        {application.role_title}
      </p>
      <p className="mt-0.5 truncate text-[13px] text-ink-soft">{application.company_name}</p>

      {application.offer_amount ? (
        <p className="tabular mt-1.5 text-[13px] text-good">
          {application.offer_currency === "INR" ? "₹" : ""}
          {application.offer_amount.toLocaleString("en-IN")}
        </p>
      ) : null}

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {application.applied_via === "referral" && <Pill tone="accent">referral</Pill>}
        {application.source && <Pill>{application.source}</Pill>}
      </div>

      <div className="mt-2.5 flex items-center gap-1">
        {next && (
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            className="px-1.5"
            onClick={() => onMove(application.id, next)}
          >
            {NEXT_LABEL[application.status]} <CaretRightIcon size={12} />
          </Button>
        )}
        {canPrep && (
          <Button
            size="sm"
            variant="ghost"
            className="px-1.5"
            aria-label={`Interview prep for ${application.role_title ?? "this role"}`}
            onClick={() => onPrep(application)}
          >
            <ChatCircleTextIcon size={13} /> Prep
          </Button>
        )}
        {application.apply_url && (
          <a
            href={application.apply_url}
            target="_blank"
            rel="noreferrer"
            aria-label="Open the posting"
            className="ml-auto flex h-8 w-8 items-center justify-center rounded-md text-ink-faint hover:bg-sunken hover:text-ink"
          >
            <ArrowSquareOutIcon size={14} />
          </a>
        )}
      </div>
    </Card>
  );
}

export function Pipeline({ onGoTo }: ViewProps) {
  const applications = useAsync(() => api.listApplications(), []);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [prepFor, setPrepFor] = useState<Application | null>(null);
  const [prep, setPrep] = useState<InterviewPrep | null>(null);
  const [prepError, setPrepError] = useState<string | null>(null);

  async function openPrep(application: Application) {
    setPrepFor(application);
    setPrep(null);
    setPrepError(null);
    try {
      setPrep(await api.interviewPrep(application.job_id!));
    } catch (e) {
      setPrepError(e instanceof ApiError ? e.message : "Could not prepare for this one");
    }
  }

  async function move(id: string, status: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.moveStage(id, status);
      applications.reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not move that");
    } finally {
      setBusyId(null);
    }
  }

  const all = applications.data?.applications ?? [];
  const closed = all.filter((a) => a.status === "accepted" || a.status === "rejected");

  return (
    <div className="grid gap-6">
      {prepFor && (
        <InterviewPanel
          prep={prep}
          loading={!prep && !prepError}
          error={prepError}
          title={`${prepFor.role_title ?? ""} at ${prepFor.company_name ?? ""}`}
          onClose={() => setPrepFor(null)}
        />
      )}

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Every application and where it stands. Moving a card sets the next date to check in.
        </p>
      </div>

      {error && <ErrorNote message={error} />}

      {applications.loading ? (
        <Loading rows={3} />
      ) : applications.error ? (
        <ErrorNote message={applications.error} onRetry={applications.reload} />
      ) : all.length ? (
        <>
          {/* Horizontal on desktop, a readable stack on a phone. */}
          <div className="-mx-4 overflow-x-auto px-4 pb-2">
            <div className="grid min-w-[1140px] grid-cols-6 gap-3">
              {COLUMNS.map((column) => {
                const cards = all.filter((a) => a.status === column.id);
                return (
                  /* Grid items default to min-width:auto, so without min-w-0 a
                     long job title pushes the card out over its neighbours. */
                  <section key={column.id} aria-label={column.label} className="min-w-0">
                    <h2 className="mb-2 flex items-baseline gap-1.5 px-0.5 text-[13px] font-medium">
                      {column.label}
                      <span className="tabular text-ink-faint">{cards.length}</span>
                    </h2>
                    <div className="grid gap-2">
                      {cards.map((application) => (
                        <ApplicationCard
                          key={application.id}
                          application={application}
                          onMove={move}
                          onPrep={openPrep}
                          busy={busyId === application.id}
                        />
                      ))}
                      {!cards.length && (
                        <div className="rounded-[--radius-card] border border-dashed px-3 py-6 text-center text-[12px] text-ink-faint">
                          Empty
                        </div>
                      )}
                    </div>
                  </section>
                );
              })}
            </div>
          </div>

          {!!closed.length && (
            <section>
              <h2 className="mb-2 text-[13px] font-medium text-ink-soft">
                Closed · {closed.length}
              </h2>
              <div className="flex flex-wrap gap-2">
                {closed.map((application) => (
                  <span
                    key={application.id}
                    className="rounded-full border px-3 py-1 text-[13px] text-ink-soft"
                  >
                    {application.company_name} · {application.status}
                  </span>
                ))}
              </div>
            </section>
          )}
        </>
      ) : (
        <Empty
          title="Nothing in the pipeline"
          hint="Track a job from the Jobs tab and it shows up here."
          action={
            <Button size="sm" onClick={() => onGoTo("jobs")}>
              Find jobs
            </Button>
          }
        />
      )}
    </div>
  );
}
