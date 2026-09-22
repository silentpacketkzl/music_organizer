import React, { useState } from "react";
import { FolderSearch, Play, ShieldAlert, Sparkles, Undo2, Copy, Check, Info } from "lucide-react";

interface ControlPanelProps {
  scanPath: string;
  setScanPath: (val: string) => void;
  isDryRun: boolean;
  setIsDryRun: (val: boolean) => void;
  onRunScan: () => void;
  onGenerateMock: () => void;
  onUndo: () => void;
  isLoading: boolean;
  testLibCount: number;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  scanPath,
  setScanPath,
  isDryRun,
  setIsDryRun,
  onRunScan,
  onGenerateMock,
  onUndo,
  isLoading,
  testLibCount,
}) => {
  const [copied, setCopied] = useState(false);

  const cliCommand = `python3 main.py --scan "${scanPath}"${isDryRun ? " --dry-run" : " --apply"}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(cliCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs">
      <div className="flex flex-col gap-4">
        {/* Top Controls: Path + Mode Toggle + Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-1 min-w-[280px] items-center gap-2">
            <div className="relative flex-1">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-zinc-400 pointer-events-none">
                <FolderSearch className="h-4 w-4" />
              </span>
              <input
                type="text"
                value={scanPath}
                onChange={(e) => setScanPath(e.target.value)}
                placeholder="/path/to/music/library"
                className="w-full rounded-lg border border-zinc-300 py-2 pl-9 pr-3 text-sm text-zinc-900 placeholder-zinc-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>

            <button
              onClick={onGenerateMock}
              disabled={isLoading}
              title="Generate 6 synthetic test tracks in /tmp/music_test with exact & acoustic duplicates"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 bg-zinc-50 px-3 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 disabled:opacity-50"
            >
              <Sparkles className="h-3.5 w-3.5 text-cyan-600" />
              Generate Test Audio ({testLibCount})
            </button>
          </div>

          <div className="flex items-center gap-3">
            {/* Safe Dry-Run Switch */}
            <div className="flex items-center rounded-lg border border-zinc-200 bg-zinc-100 p-1">
              <button
                type="button"
                onClick={() => setIsDryRun(true)}
                className={`flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                  isDryRun
                    ? "bg-white text-zinc-900 shadow-xs ring-1 ring-zinc-950/5"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
              >
                <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
                Dry-Run (Preview)
              </button>
              <button
                type="button"
                onClick={() => setIsDryRun(false)}
                className={`flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                  !isDryRun
                    ? "bg-emerald-600 text-white shadow-xs"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
              >
                <Play className="h-3.5 w-3.5" />
                Apply (Move &amp; Tag)
              </button>
            </div>

            <button
              onClick={onRunScan}
              disabled={isLoading}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-xs transition-all disabled:opacity-50 ${
                isDryRun ? "bg-cyan-600 hover:bg-cyan-700" : "bg-emerald-600 hover:bg-emerald-700"
              }`}
            >
              {isLoading ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {isDryRun ? "Simulate Deduplication" : "Execute Reorganization"}
            </button>

            <button
              onClick={onUndo}
              disabled={isLoading}
              title="Undo last organization session using SQLite audit log"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
            >
              <Undo2 className="h-3.5 w-3.5 text-zinc-500" />
              Undo Last Session
            </button>
          </div>
        </div>

        {/* CLI Terminal Command Preview Bar */}
        <div className="flex items-center justify-between gap-2 rounded-lg border border-zinc-200 bg-zinc-900 px-3.5 py-2.5 text-xs text-zinc-300 font-mono">
          <div className="flex items-center gap-2 overflow-x-auto">
            <span className="text-cyan-400 select-none">$</span>
            <span className="whitespace-nowrap">{cliCommand}</span>
          </div>
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-1 rounded-md bg-zinc-800 px-2 py-1 text-zinc-300 hover:bg-zinc-700 hover:text-white"
            title="Copy command to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Copy CLI</span>
              </>
            )}
          </button>
        </div>

        {/* Notice Bar */}
        <div className="flex items-start gap-2 rounded-lg bg-zinc-50 p-2.5 text-xs text-zinc-600">
          <Info className="h-4 w-4 shrink-0 text-cyan-600 mt-0.5" />
          <span>
            <strong>Zero Deletions Safety Guarantee:</strong> Duplicate files are never deleted directly. They are routed safely to{" "}
            <code className="rounded bg-zinc-200 px-1 py-0.5 text-zinc-800">_Duplicates_Trash</code> inside your music directory. All transactions are logged to SQLite for instant one-click rollback.
          </span>
        </div>
      </div>
    </div>
  );
};
