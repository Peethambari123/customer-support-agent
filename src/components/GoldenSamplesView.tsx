import React, { useEffect, useState } from "react";
import { Search, Play, CheckCircle, AlertOctagon, ShieldAlert } from "lucide-react";
import { GoldenSample } from "../types";

interface GoldenSamplesViewProps {
  onSelectSample: (msg: string) => void;
}

export const GoldenSamplesView: React.FC<GoldenSamplesViewProps> = ({ onSelectSample }) => {
  const [samples, setSamples] = useState<GoldenSample[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [intentFilter, setIntentFilter] = useState("ALL");

  useEffect(() => {
    fetch("/api/golden_samples")
      .then((res) => res.json())
      .then((data) => {
        setSamples(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load golden samples:", err);
        setLoading(false);
      });
  }, []);

  const intents = ["ALL", ...Array.from(new Set(samples.map((s) => s.ground_truth_intent)))];

  const filtered = samples.filter((s) => {
    const matchesSearch =
      s.customer_message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.historical_agent_reply.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesIntent = intentFilter === "ALL" || s.ground_truth_intent === intentFilter;
    return matchesSearch && matchesIntent;
  });

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-stone-900">
              Hand-Verified Golden Test Set (200 Curated Conversations)
            </h3>
            <p className="text-xs text-stone-500">
              Browse ground-truth tweets with human-verified intent annotations and escalation labels.
            </p>
          </div>
          <div className="text-xs font-medium text-stone-600 bg-stone-100 px-3 py-1 rounded-md">
            Showing {filtered.length} of {samples.length} loaded
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-stone-400" />
            <input
              type="text"
              placeholder="Search customer tweet text or historical agent replies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-stone-300 text-xs text-stone-900 focus:ring-1 focus:ring-stone-900 focus:border-stone-900"
            />
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-stone-500 whitespace-nowrap">Filter Intent:</span>
            <select
              value={intentFilter}
              onChange={(e) => setIntentFilter(e.target.value)}
              className="text-xs rounded-lg border border-stone-300 py-1.5 px-2.5 text-stone-800 bg-white"
            >
              {intents.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Samples List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-6 h-6 border-2 border-stone-200 border-t-stone-900 rounded-full animate-spin mx-auto" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-stone-500 bg-white rounded-xl border border-stone-200 text-sm">
            No matching golden set samples found.
          </div>
        ) : (
          filtered.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-stone-200 p-4 shadow-xs hover:border-stone-400 transition"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-stone-100 mb-3 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-stone-400 font-semibold">
                    Sample #{item.id}
                  </span>
                  <span className="px-2 py-0.5 rounded-full font-medium bg-stone-100 text-stone-800 border border-stone-200">
                    Intent: {item.ground_truth_intent}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full font-medium text-[11px] ${
                      item.ground_truth_escalate
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    }`}
                  >
                    {item.ground_truth_escalate ? "Ground Truth: ESCALATE" : "Ground Truth: AUTO-HANDLE"}
                  </span>
                </div>

                <button
                  onClick={() => onSelectSample(item.customer_message)}
                  className="inline-flex items-center space-x-1 px-3 py-1 rounded bg-stone-900 hover:bg-stone-800 text-white font-medium text-xs transition"
                >
                  <Play className="w-3 h-3 text-sky-400 fill-sky-400" />
                  <span>Test in Live Agent</span>
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-stone-600 block">Customer Tweet:</span>
                  <p className="text-stone-900 font-sans text-sm mt-0.5">
                    "{item.customer_message}"
                  </p>
                </div>
                {item.historical_agent_reply && (
                  <div className="pt-2 border-t border-stone-100 text-stone-600">
                    <span className="font-semibold text-stone-500 block">
                      Original AppleSupport Reply on Twitter:
                    </span>
                    <p className="italic text-stone-700 mt-0.5">
                      "{item.historical_agent_reply}"
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
