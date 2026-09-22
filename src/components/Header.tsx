import React from "react";
import { Disc3, CheckCircle2, AlertCircle, Sparkles, Terminal } from "lucide-react";
import { SystemStatus } from "../types";

interface HeaderProps {
  status: SystemStatus | null;
}

export const Header: React.FC<HeaderProps> = ({ status }) => {
  return (
    <header className="border-b border-zinc-200 bg-white px-6 py-4 shadow-xs">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-600 text-white shadow-xs">
            <Disc3 className="h-6 w-6 animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-zinc-900">
                Burmese Audio Deduper &amp; Myanglish Cleaner
              </h1>
              <span className="inline-flex items-center gap-1 rounded-md bg-cyan-50 px-2 py-0.5 text-xs font-semibold text-cyan-700 ring-1 ring-cyan-600/20">
                <Terminal className="h-3 w-3" /> CLI Engine v1.0
              </span>
            </div>
            <p className="text-xs text-zinc-500">
              MD5 &amp; Chromaprint Acoustic Waveform Deduplication • Non-Destructive Trash Routing • Burmese to Myanglish
            </p>
          </div>
        </div>

        {/* System Health Indicators */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-zinc-700">
            <span className="font-mono font-medium">fpcalc:</span>
            {status?.tools.fpcalc ? (
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <CheckCircle2 className="h-3.5 w-3.5" /> Installed
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-amber-600">
                <AlertCircle className="h-3.5 w-3.5" /> Missing
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-zinc-700">
            <span className="font-mono font-medium">ffmpeg:</span>
            {status?.tools.ffmpeg ? (
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <CheckCircle2 className="h-3.5 w-3.5" /> Ready
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-amber-600">
                <AlertCircle className="h-3.5 w-3.5" /> Missing
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-zinc-700">
            <span className="font-mono font-medium">AI Transliteration:</span>
            {status?.tools.openaiKeyConfigured ? (
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <Sparkles className="h-3.5 w-3.5" /> gpt-4o-mini
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 font-medium text-cyan-700" title="Offline phonetic rule engine active">
                <CheckCircle2 className="h-3.5 w-3.5" /> Phonetic Rule Fallback
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
