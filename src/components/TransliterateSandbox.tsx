import React, { useState } from "react";
import { Sparkles, ArrowRight, CornerDownLeft, Languages } from "lucide-react";

export const TransliterateSandbox: React.FC = () => {
  const [inputVal, setInputVal] = useState("စိုင်းထီးဆိုင်");
  const [outputVal, setOutputVal] = useState("Sai Htee Saing");
  const [loading, setLoading] = useState(false);

  const sampleChips = [
    { burmese: "စိုင်းထီးဆိုင်", title: "Sai Htee Saing" },
    { burmese: "လေးဖြူ", title: "Lay Phyu" },
    { burmese: "အချစ်ဆုတောင်း", title: "A Chit Su Taung" },
    { burmese: "နီနီခင်ဇော်", title: "Ni Ni Khin Zaw" },
    { burmese: "မင်းသိမ်း", title: "Min Thein" },
    { burmese: "သီချင်းများ", title: "Tha Chin Mya" },
  ];

  const handleTransliterate = async (textToUse?: string) => {
    const text = textToUse !== undefined ? textToUse : inputVal;
    if (!text.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("/api/transliterate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.output) {
        setOutputVal(data.output);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleChipClick = (item: { burmese: string; title: string }) => {
    setInputVal(item.burmese);
    handleTransliterate(item.burmese);
  };

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Languages className="h-4 w-4 text-cyan-600" />
          <h2 className="text-sm font-semibold text-zinc-900">
            Interactive Myanglish (Burglish) Transliteration Sandbox
          </h2>
        </div>
        <span className="text-[11px] text-zinc-500">
          Unicode &amp; Zawgyi Auto-Detection
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs text-zinc-500 font-medium">Quick samples:</span>
        {sampleChips.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleChipClick(chip)}
            className="rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs text-zinc-700 hover:bg-cyan-50 hover:border-cyan-300 hover:text-cyan-800 transition-colors"
          >
            {chip.burmese}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
        <div className="relative">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleTransliterate();
            }}
            placeholder="Type Burmese text (e.g. အချစ်)"
            className="w-full rounded-lg border border-zinc-300 py-2.5 px-3 text-sm text-zinc-900 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
          <button
            onClick={() => handleTransliterate()}
            disabled={loading}
            className="absolute right-2 top-2 rounded-md bg-zinc-100 p-1.5 text-zinc-600 hover:bg-zinc-200 disabled:opacity-50"
            title="Transliterate"
          >
            <CornerDownLeft className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/60 py-2 px-3 text-sm">
          <ArrowRight className="h-4 w-4 text-emerald-600 shrink-0" />
          <span className="font-semibold text-emerald-900">
            {loading ? "Translating..." : outputVal}
          </span>
          <span className="ml-auto rounded-full bg-emerald-200/80 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
            Myanglish
          </span>
        </div>
      </div>
    </div>
  );
};
