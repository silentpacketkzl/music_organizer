import React from "react";
import { Layers, CheckCircle, Trash2, Languages } from "lucide-react";
import { ScanResult } from "../types";

interface MetricsCardsProps {
  result: ScanResult | null;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ result }) => {
  if (!result) return null;

  const { summary, transliteration_count, elapsed_seconds } = result;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Total Scanned
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 text-zinc-700">
            <Layers className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-zinc-900">
            {summary.total_files}
          </span>
          <span className="text-xs text-zinc-500">audio tracks ({elapsed_seconds}s)</span>
        </div>
      </div>

      <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-5 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800">
            Keepers (Best Quality)
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
            <CheckCircle className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-emerald-950">
            {summary.keepers_count}
          </span>
          <span className="text-xs text-emerald-700 font-medium">Lossless / Highest Bitrate</span>
        </div>
      </div>

      <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-5 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-800">
            Flagged Duplicates
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
            <Trash2 className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-amber-950">
            {summary.duplicates_count}
          </span>
          <span className="text-xs text-amber-700 font-medium">Routed to _Duplicates_Trash</span>
        </div>
      </div>

      <div className="rounded-xl border border-cyan-100 bg-cyan-50/50 p-5 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-800">
            Myanglish Transliterations
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-100 text-cyan-700">
            <Languages className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-cyan-950">
            {transliteration_count}
          </span>
          <span className="text-xs text-cyan-700 font-medium">Burmese metadata fields updated</span>
        </div>
      </div>
    </div>
  );
};
