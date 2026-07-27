import { WarningIcon } from "@phosphor-icons/react";
import type { FitAnalysis } from "@/lib/api";
import { Pill } from "@/components/ui";

/** What the posting wants, split three ways.
 *
 *  `buried` and `missing` stay visually distinct because they call for
 *  opposite responses: rewrite for one, be honest about the other. */
export function FitPanel({ fit }: { fit: FitAnalysis }) {
  return (
    <div className="grid gap-4 border-t px-4 py-4">
      <p className="text-sm leading-relaxed">{fit.verdict}</p>

      <div className="grid gap-3 sm:grid-cols-3">
        <Group title="You already prove" tone="good" items={fit.strengths} />
        <Group title="You have, but buried" tone="accent" items={fit.buried} />
        <Group title="You genuinely lack" tone="neutral" items={fit.missing} />
      </div>

      {!!fit.suggestions.length && (
        <div className="grid gap-2">
          <h4 className="text-[13px] font-medium">What to change</h4>
          {fit.suggestions.map((suggestion, i) => (
            <div key={i} className="rounded-md bg-sunken px-3 py-2.5">
              <p className="text-[13px] leading-relaxed">
                <span className="text-ink-faint">{suggestion.section}: </span>
                {suggestion.change}
              </p>
              <p className="mt-1 text-[12px] text-ink-soft">{suggestion.why}</p>

              {!!suggestion.unsupported.length && (
                <p className="mt-2 flex items-start gap-1.5 text-[12px] text-attention">
                  <WarningIcon size={14} weight="fill" className="mt-px shrink-0" />
                  <span>
                    Your resume never mentions{" "}
                    <strong>{suggestion.unsupported.join(", ")}</strong>. Only write this if
                    it's genuinely true of you.
                  </span>
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {fit.has_unsupported && (
        <p className="text-[12px] leading-relaxed text-ink-soft">
          Some edits above lean on words from the posting rather than your resume. They're
          flagged rather than removed, because only you know what's true — but an interview
          will test anything you claim.
        </p>
      )}
    </div>
  );
}

function Group({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "good" | "accent" | "neutral";
}) {
  return (
    <div>
      <h4 className="mb-1.5 text-[12px] font-medium text-ink-soft">{title}</h4>
      {items.length ? (
        <ul className="grid gap-1">
          {items.map((item) => (
            <li key={item}>
              <Pill tone={tone}>{item}</Pill>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[12px] text-ink-faint">nothing</p>
      )}
    </div>
  );
}
