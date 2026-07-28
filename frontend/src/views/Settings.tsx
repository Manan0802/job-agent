import { useRef, useState } from "react";
import { CheckCircleIcon, CircleDashedIcon, WarningIcon } from "@phosphor-icons/react";
import { api, ApiError, type Profile, type ScheduledHunt } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, ErrorNote, Loading, SectionHeader } from "@/components/ui";
import type { ViewProps } from "@/lib/view";

function ProfileCard({ profile, onReplaced }: { profile: Profile; onReplaced: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const skills = Object.values(profile.skills ?? {}).flat();

  async function replace(file: File) {
    setBusy(true);
    setError(null);
    try {
      await api.uploadResume(file);
      onReplaced();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not read that resume");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium">{profile.personal.name ?? "Your profile"}</p>
          <p className="mt-0.5 text-sm text-ink-soft">
            {[profile.personal.email, profile.personal.location].filter(Boolean).join(" · ")}
          </p>
        </div>
        <input
          ref={input}
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) replace(file);
          }}
        />
        <Button size="sm" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Reading…" : "Replace resume"}
        </Button>
      </div>

      <dl className="mt-3 grid gap-1.5 text-[13px]">
        <div className="flex gap-2">
          <dt className="w-20 shrink-0 text-ink-faint">Skills</dt>
          <dd className="text-ink-soft">{skills.slice(0, 12).join(", ") || "none found"}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-20 shrink-0 text-ink-faint">Roles</dt>
          <dd className="text-ink-soft">
            {profile.experience.map((e) => `${e.role} at ${e.company}`).join(" · ") || "none found"}
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-20 shrink-0 text-ink-faint">Studied</dt>
          <dd className="text-ink-soft">
            {profile.education.map((e) => e.institution).filter(Boolean).join(" · ") || "none found"}
          </dd>
        </div>
      </dl>

      {error && <p className="mt-3 text-[13px] text-critical">{error}</p>}
    </Card>
  );
}

function lastHuntLine(run: ScheduledHunt): string {
  const when = new Date(run.at).toLocaleString();
  if (run.skipped) return `${when} — skipped: ${run.skipped}`;
  if (run.error) return `${when} — failed: ${run.error}`;
  if (!run.new_matches) return `${when} — ${run.total_found} jobs, nothing new`;
  const sent = run.alerted ? "messaged you" : "not messaged, alerts are off";
  return `${when} — ${run.new_matches} new of ${run.total_found}, ${sent}`;
}

export function Settings({ profile, onProfileChanged }: ViewProps) {
  const setup = useAsync(() => api.setup(), []);

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Setup</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Only the AI model is required. Everything else makes the agent better, is free, and
          the app works without it.
        </p>
      </div>

      <section>
        <SectionHeader title="Your profile" />
        <ProfileCard profile={profile} onReplaced={onProfileChanged} />
      </section>

      <section>
        <SectionHeader title="Connections" />
        {setup.loading ? (
          <Loading rows={3} />
        ) : setup.error ? (
          <ErrorNote message={setup.error} onRetry={setup.reload} />
        ) : (
          <div className="grid gap-2">
            {setup.data?.items.map((item) => (
              <Card key={item.id} className="px-4 py-3.5">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 shrink-0">
                    {item.configured ? (
                      <CheckCircleIcon size={18} weight="fill" className="text-good" />
                    ) : item.required ? (
                      <WarningIcon size={18} weight="fill" className="text-critical" />
                    ) : (
                      <CircleDashedIcon size={18} className="text-ink-faint" />
                    )}
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="font-medium">
                      {item.label}
                      {item.required && !item.configured && (
                        <span className="ml-2 text-[13px] font-normal text-critical">
                          required
                        </span>
                      )}
                    </p>
                    <p className="mt-0.5 text-[13px] leading-relaxed text-ink-soft">
                      {item.unlocks}
                    </p>

                    {item.configured && item.detail && (
                      <p className="mt-1.5 font-mono text-[12px] break-all text-ink-faint">
                        {item.detail}
                      </p>
                    )}

                    {!item.configured && (
                      <p className="mt-2 rounded-md bg-sunken px-3 py-2 text-[13px] leading-relaxed text-ink-soft">
                        {item.how}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
        {setup.data?.last_scheduled_hunt && (
          <p className="mt-2 text-[13px] text-ink-faint">
            Last automatic hunt: {lastHuntLine(setup.data.last_scheduled_hunt)}
          </p>
        )}
      </section>

      <p className="text-[13px] text-ink-faint">
        Keys live in <code className="font-mono">.env</code>, which is never committed. Restart
        the server after editing it.
      </p>
    </div>
  );
}
