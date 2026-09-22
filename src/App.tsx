import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { ControlPanel } from "./components/ControlPanel";
import { MetricsCards } from "./components/MetricsCards";
import { KeepersList } from "./components/KeepersList";
import { DuplicateList } from "./components/DuplicateList";
import { TransliterateSandbox } from "./components/TransliterateSandbox";
import { SystemStatus, ScanResult } from "./types";
import { CheckCircle2, AlertCircle, Terminal, HelpCircle, FileText, Music, Sparkles } from "lucide-react";

export default function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [scanPath, setScanPath] = useState("/tmp/music_test");
  const [isDryRun, setIsDryRun] = useState(true);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"results" | "docs">("results");
  const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);

  const showNotification = (msg: string, type: "success" | "error" | "info" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      const data: SystemStatus = await res.json();
      setStatus(data);
    } catch (err) {
      console.error("Failed to load status:", err);
    }
  };

  const runScan = async (pathOverride?: string, applyOverride?: boolean) => {
    const targetPath = pathOverride || scanPath;
    const applyVal = applyOverride !== undefined ? applyOverride : !isDryRun;

    setIsLoading(true);
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scanPath: targetPath,
          apply: applyVal,
        }),
      });

      const data = await res.json();
      if (data.error) {
        showNotification(data.error, "error");
      } else {
        setResult(data);
        if (applyVal) {
          showNotification(
            `Successfully reorganized ${data.keepers?.length || 0} tracks and routed ${data.duplicates?.length || 0} duplicates to _Duplicates_Trash.`,
            "success"
          );
        } else {
          showNotification(
            `Dry run complete! Analyzed ${data.summary?.total_files || 0} tracks. Zero files modified.`,
            "info"
          );
        }
      }
      fetchStatus();
    } catch (err: any) {
      showNotification(err.message || "Failed to execute scan", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateMock = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/generate-mock", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        showNotification("Generated synthetic Burmese audio test library in /tmp/music_test", "success");
        setScanPath("/tmp/music_test");
        await runScan("/tmp/music_test", false);
      } else {
        showNotification(data.error || "Failed to generate mock tracks", "error");
      }
    } catch (err: any) {
      showNotification(err.message || "Error generating mock library", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUndo = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/undo", { method: "POST" });
      const data = await res.json();
      if (data.status === "rollback_completed") {
        showNotification(`Rollback successful! Restored ${data.restored?.length || 0} files to original paths.`, "success");
        await runScan(scanPath, false);
      } else {
        showNotification("No previous session found in operations log to undo.", "info");
      }
    } catch (err: any) {
      showNotification(err.message || "Rollback failed", "error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Run initial scan of /tmp/music_test if exists
    runScan("/tmp/music_test", false);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 font-sans">
      <Header status={status} />

      {/* Main Container */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-6">
        {/* Notification Banner */}
        {notification && (
          <div
            className={`flex items-center justify-between rounded-lg p-3.5 text-sm shadow-xs transition-all ${
              notification.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : notification.type === "error"
                ? "bg-red-50 text-red-800 border border-red-200"
                : "bg-cyan-50 text-cyan-800 border border-cyan-200"
            }`}
          >
            <div className="flex items-center gap-2">
              {notification.type === "success" && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
              {notification.type === "error" && <AlertCircle className="h-4 w-4 text-red-600" />}
              {notification.type === "info" && <Sparkles className="h-4 w-4 text-cyan-600" />}
              <span>{notification.msg}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-xs font-semibold underline opacity-70 hover:opacity-100"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Action Controls & Mode Switch */}
        <ControlPanel
          scanPath={scanPath}
          setScanPath={setScanPath}
          isDryRun={isDryRun}
          setIsDryRun={setIsDryRun}
          onRunScan={() => runScan()}
          onGenerateMock={handleGenerateMock}
          onUndo={handleUndo}
          isLoading={isLoading}
          testLibCount={status?.testLibrary.fileCount || 0}
        />

        {/* Metrics Overview */}
        <MetricsCards result={result} />

        {/* Transliteration Sandbox */}
        <TransliterateSandbox />

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-zinc-200">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("results")}
              className={`flex items-center gap-2 border-b-2 py-3 text-sm font-semibold transition-colors ${
                activeTab === "results"
                  ? "border-cyan-600 text-cyan-700"
                  : "border-transparent text-zinc-500 hover:text-zinc-800"
              }`}
            >
              <Music className="h-4 w-4" />
              Deduplication &amp; Tagging Plan
              {result && (
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                  {result.summary.total_files}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("docs")}
              className={`flex items-center gap-2 border-b-2 py-3 text-sm font-semibold transition-colors ${
                activeTab === "docs"
                  ? "border-cyan-600 text-cyan-700"
                  : "border-transparent text-zinc-500 hover:text-zinc-800"
              }`}
            >
              <FileText className="h-4 w-4" />
              CLI Architecture &amp; Usage Guide
            </button>
          </div>
        </div>

        {/* Tab 1: Results View */}
        {activeTab === "results" && (
          <div className="space-y-6">
            {result ? (
              <>
                {/* Keepers List */}
                <KeepersList keepers={result.keepers} />

                {/* Duplicates Routed to Trash */}
                <DuplicateList
                  duplicates={result.duplicates}
                  trashDir={result.summary.trash_dir}
                />
              </>
            ) : (
              <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center">
                <Terminal className="mx-auto h-8 w-8 text-zinc-400" />
                <h3 className="mt-3 text-base font-semibold text-zinc-900">
                  Ready to scan music library
                </h3>
                <p className="mt-1 text-xs text-zinc-500 max-w-md mx-auto">
                  Click &ldquo;Generate Test Audio&rdquo; to create mock tracks or enter your audio path and click &ldquo;Simulate Deduplication&rdquo;.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Architecture & CLI Docs */}
        {activeTab === "docs" && (
          <div className="rounded-xl border border-zinc-200 bg-white p-6 space-y-6">
            <div>
              <h3 className="text-base font-bold text-zinc-900">CLI Commands &amp; Flags</h3>
              <p className="text-xs text-zinc-500 mt-1">
                Run directly in any terminal terminal without modifying source code.
              </p>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="rounded-lg bg-zinc-900 p-4 text-zinc-200 space-y-2">
                <div className="text-zinc-400"># 1. Preview changes safely without moving or modifying files (Default)</div>
                <div className="text-cyan-400">python3 main.py --scan "/path/to/my/music" --dry-run</div>
                <div className="text-zinc-400 mt-3"># 2. Execute deduplication and update tags</div>
                <div className="text-emerald-400">python3 main.py --scan "/path/to/my/music" --apply</div>
                <div className="text-zinc-400 mt-3"># 3. Custom trash folder for duplicate isolation</div>
                <div className="text-yellow-400">python3 main.py --scan "/path/to/my/music" --trash-dir "/Volumes/Backup/Trash" --apply</div>
                <div className="text-zinc-400 mt-3"># 4. Instant rollback to restore any previous session</div>
                <div className="text-purple-400">python3 main.py --undo</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-zinc-100 text-xs">
              <div>
                <h4 className="font-bold text-zinc-900 mb-2">Target File Organization Structure</h4>
                <div className="rounded-lg bg-zinc-50 p-3 font-mono text-zinc-700 space-y-1">
                  <div>Music/</div>
                  <div>└── &#123;Artist_Myanglish&#125;/</div>
                  <div>&nbsp;&nbsp;&nbsp;&nbsp;└── [&#123;Year&#125;] &#123;Album_Myanglish&#125;/</div>
                  <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── &#123;Track&#125; - &#123;Title_Myanglish&#125;.&#123;ext&#125;</div>
                </div>
              </div>

              <div>
                <h4 className="font-bold text-zinc-900 mb-2">Quality Arbiter Hierarchy</h4>
                <ul className="list-disc pl-4 space-y-1 text-zinc-600">
                  <li><strong>Lossless Priority:</strong> FLAC, ALAC, WAV, and AIFF always score higher than lossy codecs.</li>
                  <li><strong>Bitrate Ranking:</strong> 320kbps MP3 beats 192kbps and 128kbps.</li>
                  <li><strong>Metadata Completeness:</strong> Files with existing titles/artists receive score bonuses.</li>
                  <li><strong>Acoustic Threshold:</strong> Chromaprint waveform similarity &ge; 85% within &plusmn;2s duration.</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
