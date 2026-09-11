import React, { useState } from "react";
import {
  Send,
  ShieldCheck,
  AlertOctagon,
  Search,
  Sparkles,
  Layers,
  HelpCircle,
  Clock,
  ArrowRight,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RotateCcw
} from "lucide-react";
import { AgentResponse } from "../types";

interface LiveConsoleProps {
  onSelectSample?: (msg: string) => void;
}

export const LiveConsole: React.FC<LiveConsoleProps> = () => {
  const [inputMessage, setInputMessage] = useState(
    "@AppleSupport my iPhone 8 battery drops from 100% to 20% in 45 minutes after the iOS 11 update!"
  );
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const samplePresets = [
    {
      label: "Battery Drain (Auto-Handle)",
      text: "@AppleSupport my iPhone 8 battery drops from 100% to 20% in 45 minutes after the iOS 11 update!",
    },
    {
      label: "Cracked Screen (Escalate Hardware)",
      text: "@AppleSupport I dropped my iPhone on the driveway, the glass is shattered and touch isn't working.",
    },
    {
      label: "Swollen Battery (Thermal Hazard)",
      text: "@AppleSupport my MacBook battery is swollen and bulging, smells like smoke and is very hot!",
    },
    {
      label: "Account Lockout (Security Gate)",
      text: "@AppleSupport someone hacked my Apple ID and changed my recovery email to hacker@evil.com!",
    },
    {
      label: "PII Sanitization Test",
      text: "@AppleSupport please call me at 415-555-0199 or email sarah.c@company.org regarding order #982173.",
    },
  ];

  const handleProcess = async (textToRun?: string) => {
    const query = textToRun || inputMessage;
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/support/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data: AgentResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message || "Failed to process message through agent pipeline.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <label htmlFor="customer-input-textarea" className="text-sm font-semibold text-stone-900 flex items-center space-x-2">
            <span>Customer Tweet Input</span>
            <span className="text-xs font-normal text-stone-500">(@AppleSupport context)</span>
          </label>
          <div className="text-xs text-stone-500">
            {inputMessage.length} characters
          </div>
        </div>

        <div className="relative">
          <textarea
            id="customer-input-textarea"
            rows={3}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Enter an incoming tweet to @AppleSupport..."
            className="w-full rounded-lg border border-stone-300 p-3 text-sm text-stone-900 placeholder-stone-400 focus:border-stone-900 focus:ring-1 focus:ring-stone-900 font-mono resize-none transition"
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-stone-500 font-medium">Quick Presets:</span>
              {samplePresets.map((preset, idx) => (
                <button
                  key={idx}
                  id={`preset-btn-${idx}`}
                  type="button"
                  onClick={() => {
                    setInputMessage(preset.text);
                    handleProcess(preset.text);
                  }}
                  className="text-xs px-2.5 py-1 rounded-md bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            <button
              id="submit-process-btn"
              type="button"
              disabled={loading || !inputMessage.trim()}
              onClick={() => handleProcess()}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-stone-900 hover:bg-stone-800 disabled:opacity-50 text-white text-sm font-medium transition shadow-xs"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Processing Pipeline...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 text-sky-400" />
                  <span>Run Agent Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-2">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
            <div>
              <p className="font-medium">Pipeline Error</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Results Pipeline */}
      {response && (
        <div className="space-y-6">
          {/* Main Decision Banner */}
          <div
            id="decision-banner"
            className={`rounded-xl border p-5 transition-all ${
              response.escalation.decision === "AUTO-HANDLE"
                ? "bg-emerald-50/70 border-emerald-200 text-emerald-950"
                : "bg-amber-50/70 border-amber-200 text-amber-950"
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    response.escalation.decision === "AUTO-HANDLE"
                      ? "bg-emerald-600 text-white"
                      : "bg-amber-600 text-white"
                  }`}
                >
                  {response.escalation.decision === "AUTO-HANDLE" ? (
                    <ShieldCheck className="w-6 h-6" />
                  ) : (
                    <AlertOctagon className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-lg">
                      Pipeline Decision: {response.escalation.decision}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-semibold uppercase bg-white/80 border border-stone-200">
                      Intent: {response.classification.intent}
                    </span>
                  </div>
                  <p className="text-sm opacity-90 mt-0.5">
                    {response.escalation.reason}
                  </p>
                </div>
              </div>

              {response.escalation.risk_factors.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-xs font-semibold text-amber-900 mr-1">Risk Triggers:</span>
                  {response.escalation.risk_factors.map((rf, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 rounded bg-amber-200/80 text-amber-900 font-mono font-medium border border-amber-300"
                    >
                      {rf}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Generated Reply Card */}
          <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100 mb-4">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-stone-900 text-base">
                  Generated Grounded Customer Response
                </h3>
              </div>
              <div className="flex items-center space-x-2 text-xs text-stone-500">
                <span className="px-2 py-0.5 rounded bg-stone-100 font-mono">
                  Engine: {response.explanation.generation_engine}
                </span>
                <span>{response.generated_reply.length} chars</span>
              </div>
            </div>

            <div className="bg-stone-50 rounded-lg p-4 border border-stone-200">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-stone-900 text-white flex items-center justify-center font-bold text-xs shrink-0">
                  
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-semibold text-stone-900 text-sm">Apple Support</span>
                    <span className="text-stone-400 text-xs">@AppleSupport</span>
                  </div>
                  <p className="mt-1 text-sm text-stone-800 leading-relaxed font-sans">
                    {response.generated_reply}
                  </p>
                </div>
              </div>
            </div>

            {/* Audit Trail: Why this response? */}
            <div className="mt-4 pt-3 border-t border-stone-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-2 flex items-center space-x-1">
                <HelpCircle className="w-3.5 h-3.5 text-stone-400" />
                <span>Structured Audit Trail ("Why This Response?")</span>
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="bg-stone-50 rounded-lg p-2.5 border border-stone-200">
                  <span className="text-stone-500 block">Intent Classification</span>
                  <span className="font-semibold text-stone-800 text-sm">
                    {response.classification.intent}
                  </span>
                  <span className="text-stone-400 block mt-0.5">
                    Confidence: {(response.classification.confidence * 100).toFixed(0)}% (
                    {response.classification.source})
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-2.5 border border-stone-200">
                  <span className="text-stone-500 block">Retrieval Grounding</span>
                  <span className="font-semibold text-stone-800 text-sm">
                    Precedent: {response.explanation.retrieved_precedent_id || "None"}
                  </span>
                  <span className="text-stone-400 block mt-0.5">
                    Similarity: {(response.explanation.retrieval_similarity * 100).toFixed(1)}% (Threshold 18%)
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-2.5 border border-stone-200">
                  <span className="text-stone-500 block">Safety & Compliance</span>
                  <span
                    className={`font-semibold text-sm ${
                      response.explanation.safety_policy_passed
                        ? "text-emerald-700"
                        : "text-amber-700"
                    }`}
                  >
                    {response.explanation.safety_policy_passed ? "PASSED (Safe)" : "ESCALATED (Risk Gate)"}
                  </span>
                  <span className="text-stone-400 block mt-0.5">
                    PII Masking & DM Protocol Enforced
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-2.5 border border-stone-200">
                  <span className="text-stone-500 block">Cleaned Text</span>
                  <span className="font-mono text-stone-700 block truncate mt-0.5" title={response.cleaned_input}>
                    {response.cleaned_input}
                  </span>
                  <span className="text-stone-400 block mt-0.5">
                    URLs & handles normalized
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Retrieved Historical Evidence */}
          <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100 mb-4">
              <div className="flex items-center space-x-2">
                <Search className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-stone-900 text-base">
                  Retrieved Historical Precedents ({response.retrieved_evidence.length})
                </h3>
              </div>
              <div className="text-xs text-stone-500">
                Indexed from 3,979 reproducible AppleSupport threads
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {response.retrieved_evidence.map((ev, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-stone-200 p-3.5 bg-stone-50 flex flex-col justify-between text-xs space-y-3"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-stone-500 font-semibold">
                        #{idx + 1} {ev.conversation_id}
                      </span>
                      <span className="px-2 py-0.5 rounded-full font-bold bg-sky-100 text-sky-800 border border-sky-200">
                        {(ev.similarity_score * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      <div>
                        <span className="font-semibold text-stone-700 block">Historical Customer:</span>
                        <p className="text-stone-600 line-clamp-3 italic">
                          "{ev.customer_issue}"
                        </p>
                      </div>
                      <div className="pt-2 border-t border-stone-200">
                        <span className="font-semibold text-stone-700 block">Apple Agent Response:</span>
                        <p className="text-stone-800 font-sans line-clamp-3">
                          "{ev.historical_agent_response}"
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-[10px] text-stone-400 pt-1 border-t border-stone-200/60">
                    Intent: {ev.intent} • {ev.timestamp}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
