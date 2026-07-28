import { useState } from "react";
import { ArrowSquareOutIcon, MagnifyingGlassIcon, PenNibIcon } from "@phosphor-icons/react";
import { api, ApiError, type Contact } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { Button, Card, Empty, ErrorNote, Loading, Pill, SectionHeader } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { ViewProps } from "@/lib/view";

/** Warmth is a 1-5 scale, so it reads as a scale rather than a number. */
function Warmth({ score }: { score: number }) {
  return (
    <span className="flex shrink-0 items-center gap-0.5" title={`Warmth ${score} of 5`}>
      <span className="sr-only">Warmth {score} of 5</span>
      {[1, 2, 3, 4, 5].map((step) => (
        <span
          key={step}
          aria-hidden
          className={cn(
            "h-4 w-1.5 rounded-full",
            step <= score ? "bg-accent" : "bg-line",
          )}
        />
      ))}
    </span>
  );
}

function ContactCard({
  contact,
  onDraft,
  onSeeDraft,
  drafting,
}: {
  contact: Contact;
  onDraft: (contact: Contact) => void;
  onSeeDraft: () => void;
  drafting: boolean;
}) {
  const status = contact.outreach_status;
  // A draft is unfinished business, so it stays actionable; sent and skipped
  // are done and just report themselves.
  const drafted = status === "drafted";
  const finished = status === "sent" || status === "skipped";

  return (
    <Card className="px-4 py-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-medium">{contact.name}</h3>
          <p className="mt-0.5 truncate text-sm text-ink-soft">
            {contact.current_role ?? "Role unknown"}
            {contact.current_company ? ` · ${contact.current_company}` : ""}
          </p>
        </div>
        <Warmth score={contact.warmth_score ?? 1} />
      </div>

      {!!contact.warmth_reasons.length && (
        <p className="mt-2 text-[13px] leading-relaxed text-ink-soft">
          {contact.warmth_reasons.join(" · ")}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {finished ? (
          <Pill tone={status === "sent" ? "good" : "neutral"}>{status}</Pill>
        ) : drafted ? (
          <Button size="sm" onClick={onSeeDraft}>
            <PenNibIcon size={14} /> See your draft
          </Button>
        ) : (
          <Button size="sm" variant="primary" disabled={drafting} onClick={() => onDraft(contact)}>
            <PenNibIcon size={14} />
            {drafting ? "Writing…" : "Draft message"}
          </Button>
        )}
        {contact.linkedin_url && (
          <a
            href={contact.linkedin_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-[13px] font-medium text-ink-soft hover:bg-sunken hover:text-ink"
          >
            Profile <ArrowSquareOutIcon size={14} />
          </a>
        )}
        <span className="ml-auto flex gap-1">
          {contact.degree_type === "1st" && <Pill tone="accent">You know them</Pill>}
          {contact.source && <Pill>{contact.source}</Pill>}
        </span>
      </div>
    </Card>
  );
}

export function Referrals({ onGoTo }: ViewProps) {
  const saved = useAsync(() => api.listReferrals(), []);
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manualUrl, setManualUrl] = useState<string | null>(null);
  const [draftingId, setDraftingId] = useState<string | null>(null);

  async function find() {
    setSearching(true);
    setError(null);
    setManualUrl(null);
    try {
      const result = await api.findReferrals(company.trim(), role.trim() || undefined);
      setManualUrl(result.manual_search_url);
      saved.reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The search failed");
    } finally {
      setSearching(false);
    }
  }

  async function draft(contact: Contact) {
    setDraftingId(contact.id);
    setError(null);
    try {
      await api.draftOutreach(contact.id);
      onGoTo("outreach");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not write that message");
    } finally {
      setDraftingId(null);
    }
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Referrals</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Who could get you in, warmest first. Pulled from your own LinkedIn export and public
          search, with the reason for every ranking.
        </p>
      </div>

      <Card className="flex flex-wrap items-end gap-3 p-4">
        <label className="grid min-w-[190px] flex-1 gap-1.5">
          <span className="text-[13px] font-medium">Company</span>
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Zepto"
            className="h-9 rounded-md border bg-surface px-3 text-sm placeholder:text-ink-faint"
          />
        </label>
        <label className="grid min-w-[150px] flex-1 gap-1.5">
          <span className="text-[13px] font-medium">Role (optional)</span>
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="SDE-2 Backend"
            className="h-9 rounded-md border bg-surface px-3 text-sm placeholder:text-ink-faint"
          />
        </label>
        <Button variant="primary" onClick={find} disabled={searching || !company.trim()}>
          <MagnifyingGlassIcon size={15} />
          {searching ? "Looking…" : "Find people"}
        </Button>
      </Card>

      {error && <ErrorNote message={error} />}

      {manualUrl && (
        <p className="text-sm text-ink-soft">
          Want to look yourself too?{" "}
          <a href={manualUrl} target="_blank" rel="noreferrer" className="text-accent underline">
            Open this search on LinkedIn
          </a>
          .
        </p>
      )}

      <section>
        <SectionHeader title="People who could refer you" count={saved.data?.count} />
        {saved.loading ? (
          <Loading rows={3} />
        ) : saved.error ? (
          <ErrorNote message={saved.error} onRetry={saved.reload} />
        ) : saved.data?.contacts.length ? (
          <div className="grid gap-2">
            {saved.data.contacts.map((contact) => (
              <ContactCard
                key={contact.id}
                contact={contact}
                drafting={draftingId === contact.id}
                onDraft={draft}
                onSeeDraft={() => onGoTo("outreach")}
              />
            ))}
          </div>
        ) : (
          <Empty
            title="No contacts yet"
            hint="Search a company above. Add your LinkedIn connections export to also surface people you already know."
          />
        )}
      </section>
    </div>
  );
}
