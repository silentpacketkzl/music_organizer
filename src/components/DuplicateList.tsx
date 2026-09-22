import React from "react";
import { Trash2, AlertTriangle, FileAudio, ArrowRight, ShieldCheck } from "lucide-react";
import { TrashAction } from "../types";

interface DuplicateListProps {
  duplicates: TrashAction[];
  trashDir?: string;
}

export const DuplicateList: React.FC<DuplicateListProps> = ({ duplicates, trashDir }) => {
  if (duplicates.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-300 bg-white p-8 text-center">
        <ShieldCheck className="mx-auto h-8 w-8 text-emerald-500" />
        <h3 className="mt-2 text-sm font-semibold text-zinc-900">No Duplicates Flagged</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Every audio file in the scanned collection has a unique acoustic fingerprint and MD5 hash.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-white shadow-xs overflow-hidden">
      <div className="border-b border-amber-200 bg-amber-50/60 px-5 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trash2 className="h-4 w-4 text-amber-600" />
          <h2 className="text-sm font-semibold text-zinc-900">
            Flagged Duplicates Isolated ({duplicates.length})
          </h2>
        </div>
        <span className="text-xs text-amber-800 font-medium">
          Routed safely to {trashDir || "_Duplicates_Trash"}
        </span>
      </div>

      <div className="divide-y divide-zinc-100">
        {duplicates.map((item, idx) => {
          const { file_info, reason, source, destination } = item;
          const isExact = reason.toLowerCase().includes("exact md5");

          return (
            <div key={idx} className="p-4 hover:bg-zinc-50/50 transition-colors">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-amber-100 font-mono text-xs font-bold text-amber-800 mt-0.5">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-medium text-zinc-800 truncate max-w-sm" title={source}>
                        {source.split("/").pop()}
                      </span>
                      {isExact ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">
                          EXACT MD5 DUPLICATE
                        </span>
                      ) : (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                          ACOUSTIC MATCH (CHROMAPRINT)
                        </span>
                      )}
                    </div>

                    <p className="mt-1 text-xs text-red-600 font-medium flex items-center gap-1.5">
                      <AlertTriangle className="h-3 w-3 shrink-0" />
                      {reason}
                    </p>

                    <div className="mt-1 flex items-center gap-2 text-[11px] text-zinc-400 font-mono">
                      <span>{file_info.format} {file_info.bitrate}kbps</span>
                      <span>•</span>
                      <span>{Math.round(file_info.duration)}s</span>
                      <span>•</span>
                      <span>{(file_info.file_size / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                </div>

                <div className="text-right text-[11px] font-mono text-zinc-400">
                  <span className="rounded bg-zinc-100 px-2 py-1 text-zinc-600">
                    MD5: {file_info.md5_hash.slice(0, 10)}...
                  </span>
                </div>
              </div>

              <div className="mt-2 text-[11px] font-mono text-zinc-400 truncate">
                <span>Relocated to: </span>
                <span className="text-amber-700">{destination}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
