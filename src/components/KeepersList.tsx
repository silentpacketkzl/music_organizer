import React from "react";
import { CheckCircle, Music2, ArrowRight, Disc, Mic2, Tag } from "lucide-react";
import { KeeperAction } from "../types";

interface KeepersListProps {
  keepers: KeeperAction[];
}

export const KeepersList: React.FC<KeepersListProps> = ({ keepers }) => {
  if (keepers.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white shadow-xs overflow-hidden">
      <div className="border-b border-zinc-200 bg-zinc-50/70 px-5 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-600" />
          <h2 className="text-sm font-semibold text-zinc-900">
            Keepers &amp; Myanglish Metadata Tagging ({keepers.length})
          </h2>
        </div>
        <span className="text-xs text-zinc-500 font-medium">
          Highest Quality Preserved (FLAC &gt; MP3)
        </span>
      </div>

      <div className="divide-y divide-zinc-100">
        {keepers.map((item, idx) => {
          const { file_info, old_tags, new_tags, source, destination } = item;
          const isLossless = Boolean(file_info.is_lossless);

          return (
            <div key={idx} className="p-5 hover:bg-zinc-50/50 transition-colors">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-emerald-100 font-mono text-xs font-bold text-emerald-800">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-zinc-900">
                        {new_tags.title || "Untitled"}
                      </span>
                      {isLossless ? (
                        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-800">
                          LOSSLESS {file_info.format}
                        </span>
                      ) : (
                        <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] font-semibold text-zinc-700">
                          {file_info.format} {file_info.bitrate}kbps
                        </span>
                      )}
                      <span className="text-xs text-zinc-400 font-mono">
                        {Math.round(file_info.duration)}s
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500 flex items-center gap-1.5 mt-0.5">
                      <Mic2 className="h-3 w-3 text-zinc-400" />
                      <span className="font-medium text-zinc-700">{new_tags.artist}</span>
                      <span className="text-zinc-300">•</span>
                      <Disc className="h-3 w-3 text-zinc-400" />
                      <span>[{new_tags.year}] {new_tags.album}</span>
                      <span className="text-zinc-300">•</span>
                      <span>Track {new_tags.track}</span>
                    </p>
                  </div>
                </div>

                {/* Quality Score details */}
                <div className="text-right text-xs">
                  <span className="inline-block rounded-md bg-zinc-100 px-2.5 py-1 font-mono font-medium text-zinc-700">
                    {file_info.sample_rate}Hz • {file_info.channels === 2 ? "Stereo" : "Mono"}
                  </span>
                </div>
              </div>

              {/* Tag diff comparison */}
              <div className="mt-3.5 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
                      Title Transliteration
                    </span>
                    <div className="flex items-center gap-1.5 font-medium">
                      <span className="text-zinc-600 font-burmese">{old_tags.title || "—"}</span>
                      <ArrowRight className="h-3 w-3 text-zinc-400 shrink-0" />
                      <span className="text-emerald-700 font-semibold">{new_tags.title}</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
                      Artist Transliteration
                    </span>
                    <div className="flex items-center gap-1.5 font-medium">
                      <span className="text-zinc-600 font-burmese">{old_tags.artist || "—"}</span>
                      <ArrowRight className="h-3 w-3 text-zinc-400 shrink-0" />
                      <span className="text-emerald-700 font-semibold">{new_tags.artist}</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
                      Album Transliteration
                    </span>
                    <div className="flex items-center gap-1.5 font-medium">
                      <span className="text-zinc-600 font-burmese">{old_tags.album || "—"}</span>
                      <ArrowRight className="h-3 w-3 text-zinc-400 shrink-0" />
                      <span className="text-emerald-700 font-semibold">{new_tags.album}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Target reorganized file path */}
              <div className="mt-2 text-[11px] font-mono text-zinc-500 truncate" title={destination}>
                <span className="text-zinc-400">Target: </span>
                <span className="text-cyan-700">{destination}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
