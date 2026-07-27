import { ArrowRightIcon } from "@phosphor-icons/react";
import { api, type Profile } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill, SectionHeader } from "@/components/ui";

type Props = { profile: Profile; onGoTo: (view: never) => void };

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="px-4 py-3.5">
      <span className="tabular block text-2xl leading-tight">{value}</span>
      <span className="mt-0.5 block text-[13px] text-ink-soft">{label}</span>
      {hint && <span className="mt-0.5 block text-[11px] text-ink-faint">{hint}</span>}
    </div>
  );
}

export function Today({ profile, onGoTo }: Props) {
  const stats = useAsync(() => api.stats(), []);
  const reminders = useAsync(() => api.reminders(), []);
  const drafts = useAsync(() => api.listOutreach("draft"), []);

  const firstName = profile.personal.name?.split(" ")[0];

  return (
    <div className="grid gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {firstName ? `Hey ${firstName}` : "Your job hunt"}
        </h1>
        <p className="mt-1 text-sm text-ink-soft">Here's what's waiting on you.</p>
      </div>

      {/* Anything overdue is the reason to open this app, so it leads. */}
      <section>
        <SectionHeader title="Needs a nudge" count={reminders.data?.count} />
        {reminders.loading ? (
          <Loading rows={2} />
        ) : reminders.error ? (
          <ErrorNote message={reminders.error} onRetry={reminders.reload} />
        ) : reminders.data?.reminders.length ? (
          <div className="grid gap-2">
            {reminders.data.reminders.map((reminder) => (
              <Card
                key={reminder.id}
                className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">
                    {reminder.role_title} · {reminder.company_name}
                  </p>
                  <p className="mt-0.5 text-sm text-ink-soft">{reminder.action}</p>
                </div>
                <Pill tone={reminder.days_overdue > 7 ? "critical" : "attention"}>
                  {reminder.days_overdue}d overdue
                </Pill>
              </Card>
            ))}
          </div>
        ) : (
          <Empty
            quiet
            title="Nothing overdue."
            hint="Everything you're tracking has been touched recently."
          />
        )}
      </section>

      <section>
        <SectionHeader title="Drafts waiting for you" count={drafts.data?.count}>
          {!!drafts.data?.count && (
            <Button size="sm" onClick={() => onGoTo("outreach" as never)}>
              Review <ArrowRightIcon size={14} />
            </Button>
          )}
        </SectionHeader>
        {drafts.loading ? (
          <Loading rows={1} />
        ) : drafts.error ? (
          <ErrorNote message={drafts.error} onRetry={drafts.reload} />
        ) : drafts.data?.messages.length ? (
          <div className="grid gap-2">
            {drafts.data.messages.slice(0, 3).map((message) => (
              <Card key={message.id} className="px-4 py-3">
                <p className="font-medium">To {message.contact_name ?? "a contact"}</p>
                <p className="mt-1 line-clamp-2 text-sm text-ink-soft">{message.body}</p>
              </Card>
            ))}
          </div>
        ) : (
          <Empty
            title="No drafts right now"
            hint="Find someone who can refer you, then draft a message to them."
            action={
              <Button size="sm" onClick={() => onGoTo("referrals" as never)}>
                Find referrals
              </Button>
            }
          />
        )}
      </section>

      <section>
        <SectionHeader title="How it's going" />
        {stats.loading ? (
          <Loading rows={1} />
        ) : stats.error ? (
          <ErrorNote message={stats.error} onRetry={stats.reload} />
        ) : stats.data && stats.data.total > 0 ? (
          <Card className="grid grid-cols-2 divide-x divide-y overflow-hidden sm:grid-cols-4 sm:divide-y-0">
            <Stat label="In the pipeline" value={String(stats.data.active)} />
            <Stat label="Applied" value={String(stats.data.applied)} />
            <Stat
              label="Heard back"
              value={`${stats.data.response_rate}%`}
              hint={`${stats.data.responded} of ${stats.data.applied}`}
            />
            <Stat
              label="Offers"
              value={String(stats.data.offers)}
              hint={stats.data.best_source ? `best: ${stats.data.best_source}` : undefined}
            />
          </Card>
        ) : (
          <Empty
            title="Nothing tracked yet"
            hint="Once you start tracking jobs, your response rate and best source show up here."
            action={
              <Button size="sm" onClick={() => onGoTo("jobs" as never)}>
                Find jobs
              </Button>
            }
          />
        )}
      </section>
    </div>
  );
}
