import { useEffect, useRef } from "react";
import { WarningIcon, XIcon } from "@phosphor-icons/react";
import type { InterviewPrep } from "@/lib/api";
import { Loading } from "@/components/ui";

/** Prep for one interview, in a dialog.
 *
 *  A dialog rather than an inline panel because pipeline cards sit in narrow
 *  kanban columns and this is a page of reading. `<dialog>` is used natively so
 *  focus trapping, Escape and the backdrop come from the browser. */
export function InterviewPanel({
  prep,
  loading,
  error,
  title,
  onClose,
}: {
  prep: InterviewPrep | null;
  loading: boolean;
  error: string | null;
  title: string;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onClick={(e) => {
        // Clicking the backdrop lands on the dialog itself, not its content.
        if (e.target === dialog.current) dialog.current?.close();
      }}
      className="m-auto w-[min(46rem,calc(100vw-2rem))] rounded-lg border bg-raised p-0 text-ink backdrop:bg-black/40"
    >
      <div className="sticky top-0 flex items-start justify-between gap-3 border-b bg-raised px-5 py-3.5">
        <div className="min-w-0">
          <h2 className="truncate font-medium">Interview prep</h2>
          <p className="mt-0.5 truncate text-[13px] text-ink-soft">{title}</p>
        </div>
        <button
          onClick={() => dialog.current?.close()}
          aria-label="Close"
          className="-mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-ink-faint hover:bg-sunken hover:text-ink"
        >
          <XIcon size={16} />
        </button>
      </div>

      <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
        {loading && <Loading rows={5} />}

        {error && <p className="text-[13px] text-critical">{error}</p>}

        {prep && (
          <div className="grid gap-5">
            {prep.role_focus && (
              <p className="text-sm leading-relaxed">{prep.role_focus}</p>
            )}

            <section className="grid gap-2.5">
              <h3 className="text-[13px] font-medium">Expect to be asked</h3>
              {prep.questions.map((q, i) => (
                <div key={i} className="rounded-md bg-sunken px-3.5 py-3">
                  <p className="text-[13px] leading-relaxed font-medium">{q.question}</p>
                  {q.answer_from && (
                    <p className="mt-1.5 text-[13px] leading-relaxed text-ink-soft">
                      <span className="text-ink-faint">Answer from: </span>
                      {q.answer_from}
                    </p>
                  )}
                  {q.why && <p className="mt-1 text-[12px] text-ink-faint">{q.why}</p>}

                  {!!q.unsupported.length && (
                    <p className="mt-2 flex items-start gap-1.5 text-[12px] text-attention">
                      <WarningIcon size={14} weight="fill" className="mt-px shrink-0" />
                      <span>
                        Your resume never mentions{" "}
                        <strong>{q.unsupported.join(", ")}</strong>. Don't rehearse it — you
                        can't take it back once you've said it out loud.
                      </span>
                    </p>
                  )}
                </div>
              ))}
            </section>

            {!!prep.weak_spots.length && (
              <section className="grid gap-1.5">
                <h3 className="text-[13px] font-medium">Where they'll push</h3>
                <p className="text-[12px] text-ink-faint">
                  The posting wants these and your resume doesn't show them. Being ready with
                  an honest answer beats being surprised.
                </p>
                <ul className="grid gap-1.5">
                  {prep.weak_spots.map((spot, i) => (
                    <li key={i} className="text-[13px] leading-relaxed text-ink-soft">
                      · {spot}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {!!prep.ask_them.length && (
              <section className="grid gap-1.5">
                <h3 className="text-[13px] font-medium">Worth asking them</h3>
                <ul className="grid gap-1.5">
                  {prep.ask_them.map((question, i) => (
                    <li key={i} className="text-[13px] leading-relaxed text-ink-soft">
                      · {question}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )}
      </div>
    </dialog>
  );
}
