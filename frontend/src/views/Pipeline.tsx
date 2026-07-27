import { useState } from "react";
import { ArrowSquareOutIcon, CaretRightIcon } from "@phosphor-icons/react";
import { api, ApiError, type Application } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill } from "@/components/ui";

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
  busy,
}: {
  application: Application;
  onMove: (id: string, status: string) => void;
  busy: boolean;
}) {
  const next = NEXT_STAGE[application.status];

  return (
    <Card className="px-3 py-2.5">
      <p className="truncate text-[13px] font-medium">{application.role_title}</p>
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

export function Pipeline({ onGoTo }: { onGoTo: (view: never) => void }) {
  const applications = useAsync(() => api.listApplications(), []);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
            <div className="grid min-w-[900px] grid-cols-6 gap-3">
              {COLUMNS.map((column) => {
                const cards = all.filter((a) => a.status === column.id);
                return (
                  <section key={column.id} aria-label={column.label}>
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
            <Button size="sm" onClick={() => onGoTo("jobs" as never)}>
              Find jobs
            </Button>
          }
        />
      )}
    </div>
  );
}
