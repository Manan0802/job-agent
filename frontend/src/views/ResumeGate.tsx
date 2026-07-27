import { useRef, useState } from "react";
import { FilePdfIcon } from "@phosphor-icons/react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, ErrorNote } from "@/components/ui";

/** Everything else reads the profile, so this is the first thing to do. */
export function ResumeGate({ onLoaded }: { onLoaded: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      await api.uploadResume(file);
      onLoaded();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not read that resume");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg pt-10">
      <Card className="grid justify-items-center gap-4 px-6 py-12 text-center">
        <FilePdfIcon size={30} className="text-ink-faint" />
        <div className="grid gap-1.5">
          <h1 className="text-xl font-semibold">Start with your resume</h1>
          <p className="text-sm text-ink-soft">
            It becomes the profile every job score, referral match and message is written
            against. Nothing leaves your machine except the text sent to the model.
          </p>
        </div>

        <input
          ref={input}
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload(file);
          }}
        />
        <Button variant="primary" onClick={() => input.current?.click()} disabled={busy}>
          {busy ? "Reading your resume…" : "Choose a PDF"}
        </Button>

        {error && <ErrorNote message={error} />}
      </Card>
    </div>
  );
}
