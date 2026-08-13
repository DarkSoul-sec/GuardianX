import { useMemo, useState, type FormEvent } from "react";
import { Plug, ShieldCheck, Trash2 } from "lucide-react";

import VirusTotalConnectionPill from "@/components/virustotal/VirusTotalConnectionPill";

import {
  useVirusTotalConnect,
  useVirusTotalDisconnect,
  useVirusTotalStatus,
  useVirusTotalTest,
} from "@/hooks/useVirusTotal";
import { useToastContext } from "@/hooks/useToastContext";

import {
  Button,
  Card,
  Input,
  Modal,
  Skeleton,
} from "@/shared/components";
import { formatDate } from "@/shared/utils/format";

const MASKED_KEY = "vt••••••••••••••••••••••••••";

export default function VirusTotalSettingsCard() {
  const { data, isLoading } = useVirusTotalStatus();
  const connect = useVirusTotalConnect();
  const test = useVirusTotalTest();
  const disconnect = useVirusTotalDisconnect();
  const { success, error } = useToastContext();

  const [apiKey, setApiKey] = useState("");
  const [candidateResult, setCandidateResult] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const configured = data?.configured ?? false;
  const storedState = data?.status ?? "not_configured";

  const keyValid = useMemo(() => apiKey.trim().length >= 32, [apiKey]);

  function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!keyValid) {
      error("VirusTotal API keys are at least 32 characters long.");
      return;
    }

    connect.mutate(apiKey.trim(), {
      onSuccess: (response) => {
        success("VirusTotal API key saved.");
        setApiKey("");
        setCandidateResult(null);
        if (response.status.status === "invalid") {
          error(response.status.message);
        }
      },
      onError: () => error("Failed to save the VirusTotal API key."),
    });
  }

  function handleTest() {
    const candidate = apiKey.trim();

    test.mutate(candidate.length > 0 ? candidate : undefined, {
      onSuccess: (response) => {
        setCandidateResult(response.status.message);
        success(response.status.message);
      },
      onError: () => error("Failed to test the VirusTotal API key."),
    });
  }

  function handleRemove() {
    disconnect.mutate(undefined, {
      onSuccess: () => {
        success("VirusTotal API key removed.");
        setApiKey("");
        setCandidateResult(null);
        setConfirmOpen(false);
      },
      onError: () => error("Failed to remove the VirusTotal API key."),
    });
  }

  return (
    <Card className="p-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="rounded-2xl border border-cyan-400/40 bg-cyan-500/10 p-4 text-cyan-300">
            <Plug size={26} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">VirusTotal</h2>
            <p className="mt-1 text-sm text-slate-400">
              Bring your own VirusTotal API key for reputation lookups.
            </p>
          </div>
        </div>

        {isLoading ? (
          <Skeleton className="h-8 w-36" />
        ) : (
          <VirusTotalConnectionPill state={storedState} />
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-1/2" />
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-6">
          <div>
            <label
              htmlFor="virustotal-api-key"
              className="mb-2 block text-sm font-semibold text-slate-300"
            >
              API Key
            </label>

            {configured ? (
              <div className="mb-3 flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
                <ShieldCheck size={16} className="text-emerald-400" />
                <span className="font-mono">{MASKED_KEY}</span>
              </div>
            ) : null}

            <Input
              id="virustotal-api-key"
              type="password"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setCandidateResult(null);
              }}
              placeholder={
                configured
                  ? "Paste a new key to replace the stored one"
                  : "Paste your VirusTotal API key (starts with vt…)"
              }
              autoComplete="off"
              spellCheck={false}
              minLength={32}
            />
            <p className="mt-2 text-xs text-slate-500">
              Keys are encrypted before storage and never exposed again. Get a
              free key at{" "}
              <a
                href="https://www.virustotal.com/gui/my-apikey"
                target="_blank"
                rel="noreferrer"
                className="text-cyan-400 hover:underline"
              >
                virustotal.com/gui/my-apikey
              </a>
              .
            </p>
          </div>

          {data?.message ? (
            <div className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
              {data.message}
              {data.last_tested_at
                ? ` Last tested ${formatDate(data.last_tested_at)}.`
                : ""}
            </div>
          ) : null}

          {candidateResult ? (
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-200">
              {candidateResult}
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={connect.isPending || !keyValid}>
              {connect.isPending ? "Saving..." : "Save Key"}
            </Button>

            <Button
              type="button"
              variant="secondary"
              disabled={test.isPending}
              onClick={handleTest}
            >
              {test.isPending ? "Testing..." : "Test Connection"}
            </Button>

            {configured && (
              <Button
                type="button"
                variant="danger"
                disabled={disconnect.isPending}
                onClick={() => setConfirmOpen(true)}
              >
                <Trash2 size={16} className="mr-2 inline" />
                {disconnect.isPending ? "Removing..." : "Remove Key"}
              </Button>
            )}
          </div>
        </form>
      )}

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        titleId="remove-virustotal-key-title"
      >
        <div className="max-w-md p-8">
          <h2
            id="remove-virustotal-key-title"
            className="text-xl font-bold text-red-500"
          >
            Remove VirusTotal Key
          </h2>
          <p className="mt-4 text-slate-300">
            Are you sure you want to remove your stored VirusTotal API key?
            Reputation lookups will stop working until a new key is saved.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={disconnect.isPending}
              onClick={handleRemove}
            >
              {disconnect.isPending ? "Removing..." : "Remove"}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
}
