import { useState } from "react";
import { ArrowSquareOutIcon, CheckIcon, CopyIcon, XIcon } from "@phosphor-icons/react";
import { api, ApiError, type Message } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill, SectionHeader } from "@/components/ui";

const STATUS_TONE = {
  draft: "attention",
  approved: "accent",
  sent: "good",
  skipped: "neutral",
} as const;

function MessageCard({ message, onChanged }: { message: Message; onChanged: () => void }) {
  const [body, setBody] = useState(message.body ?? "");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const edited = body !== (message.body ?? "");
  const readOnly = message.status === "sent" || message.status === "skipped";

  async function act(run: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await run();
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't work");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    await navigator.clipboard.writeText(body);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b px-4 py-3">
        <div className="min-w-0">
          <p className="truncate font-medium">To {message.contact_name ?? "a contact"}</p>
          <p className="mt-0.5 text-[13px] text-ink-soft">
            {message.channel === "email" ? "Email" : "LinkedIn DM"}
            {message.message_type ? ` · ${message.message_type.replace(/_/g, " ")}` : ""}
          </p>
        </div>
        <Pill tone={STATUS_TONE[message.status as keyof typeof STATUS_TONE] ?? "neutral"}>
          {message.status}
        </Pill>
      </div>

      {message.subject && (
        <p className="border-b px-4 py-2 text-sm">
          <span className="text-ink-faint">Subject: </span>
          {message.subject}
        </p>
      )}

      <label className="block">
        <span className="sr-only">Message body</span>
        <textarea
          value={body}
          readOnly={readOnly}
          onChange={(e) => setBody(e.target.value)}
          rows={Math.min(14, body.split("\n").length + 2)}
          className="w-full resize-y bg-surface px-4 py-3 text-sm leading-relaxed text-ink read-only:text-ink-soft focus:outline-none"
        />
      </label>

      <p className="border-t bg-sunken px-4 py-2.5 text-[13px] text-ink-soft">
        {message.send.instructions}
      </p>

      {error && (
        <p className="border-t bg-critical-soft px-4 py-2.5 text-[13px] text-critical">{error}</p>
      )}

      {!readOnly && (
        <div className="flex flex-wrap items-center gap-2 border-t px-4 py-3">
          {edited && (
            <Button size="sm" disabled={busy} onClick={() => act(() => api.editOutreach(message.id, body))}>
              Save edits
            </Button>
          )}

          <Button size="sm" onClick={copy}>
            {copied ? <><CheckIcon size={14} /> Copied</> : <><CopyIcon size={14} /> Copy</>}
          </Button>

          {message.send.url && (
            <a
              href={message.send.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-8 items-center gap-1.5 rounded-md border bg-surface px-2.5 text-[13px] font-medium hover:bg-sunken"
            >
              {message.send.action === "open_mail_client" ? "Open email" : "Open profile"}
              <ArrowSquareOutIcon size={14} />
            </a>
          )}

          <span className="ml-auto flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              disabled={busy}
              onClick={() => act(() => api.skipOutreach(message.id))}
            >
              <XIcon size={14} /> Skip
            </Button>
            {message.status === "draft" ? (
              <Button
                size="sm"
                disabled={busy || edited}
                title={edited ? "Save your edits first" : undefined}
                onClick={() => act(() => api.approveOutreach(message.id))}
              >
                Approve
              </Button>
            ) : (
              <Button
                size="sm"
                variant="primary"
                disabled={busy}
                onClick={() => act(() => api.markOutreachSent(message.id))}
              >
                <CheckIcon size={14} /> I sent it
              </Button>
            )}
          </span>
        </div>
      )}
    </Card>
  );
}

export function Outreach({ onGoTo }: { onGoTo: (view: never) => void }) {
  const messages = useAsync(() => api.listOutreach(), []);

  const open = messages.data?.messages.filter((m) => m.status === "draft" || m.status === "approved") ?? [];
  const done = messages.data?.messages.filter((m) => m.status === "sent" || m.status === "skipped") ?? [];

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Outreach</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Read every message before it goes out. Nothing here sends on its own, by design.
        </p>
      </div>

      {messages.loading ? (
        <Loading rows={2} />
      ) : messages.error ? (
        <ErrorNote message={messages.error} onRetry={messages.reload} />
      ) : messages.data?.count ? (
        <>
          <section>
            <SectionHeader title="Waiting on you" count={open.length} />
            {open.length ? (
              <div className="grid gap-3">
                {open.map((message) => (
                  <MessageCard key={message.id} message={message} onChanged={messages.reload} />
                ))}
              </div>
            ) : (
              <Empty title="All caught up" hint="Nothing is waiting for your review." />
            )}
          </section>

          {!!done.length && (
            <section>
              <SectionHeader title="Already handled" count={done.length} />
              <div className="grid gap-3">
                {done.map((message) => (
                  <MessageCard key={message.id} message={message} onChanged={messages.reload} />
                ))}
              </div>
            </section>
          )}
        </>
      ) : (
        <Empty
          title="No messages yet"
          hint="Pick someone from your referrals and draft a message to them."
          action={
            <Button size="sm" onClick={() => onGoTo("referrals" as never)}>
              Go to referrals
            </Button>
          }
        />
      )}
    </div>
  );
}
