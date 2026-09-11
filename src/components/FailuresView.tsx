import React, { useEffect, useState } from "react";
import { AlertTriangle, Wrench, Bug, ArrowRight, Lightbulb } from "lucide-react";
import { FailureCase } from "../types";

export const FailuresView: React.FC = () => {
  const [failures, setFailures] = useState<FailureCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/failures")
      .then((res) => res.json())
      .then((data) => {
        setFailures(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load failures:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-8 h-8 border-4 border-stone-200 border-t-stone-900 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-stone-900 mb-1">
          <Bug className="w-5 h-5 text-amber-600" />
          <h3 className="text-base font-bold">
            Real Pipeline Failure Cases & Architectural Root Causes
          </h3>
        </div>
        <p className="text-xs text-stone-500">
          In-depth qualitative analysis of empirical errors discovered during evaluation, paired with hypotheses and concrete remediation fixes.
        </p>
      </div>

      <div className="space-y-4">
        {failures.map((item) => (
          <div
            key={item.failure_id}
            className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-stone-100">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold text-stone-400">
                  Case #{item.failure_id}
                </span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-200">
                  {item.category.replace("_", " ")}
                </span>
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-stone-500 block">Customer Input:</span>
              <p className="text-sm font-medium text-stone-900 bg-stone-50 p-2.5 rounded-lg border border-stone-200 mt-1">
                "{item.customer_input}"
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-emerald-50/70 border border-emerald-200">
                <span className="font-bold text-emerald-900 block mb-1">
                  Expected Desired Behavior:
                </span>
                <pre className="font-mono text-[11px] text-emerald-800 whitespace-pre-wrap">
                  {typeof item.expected_output === "object"
                    ? JSON.stringify(item.expected_output, null, 2)
                    : item.expected_output}
                </pre>
              </div>

              <div className="p-3 rounded-lg bg-rose-50/70 border border-rose-200">
                <span className="font-bold text-rose-900 block mb-1">
                  Actual Agent Pipeline Output:
                </span>
                <pre className="font-mono text-[11px] text-rose-800 whitespace-pre-wrap">
                  {typeof item.actual_output === "object"
                    ? JSON.stringify(item.actual_output, null, 2)
                    : item.actual_output}
                </pre>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-stone-50 border border-stone-200 space-y-2 text-xs">
              <div>
                <span className="font-bold text-stone-700 flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  <span>Why It Failed (Root Cause Hypothesis):</span>
                </span>
                <p className="text-stone-600 mt-0.5 leading-relaxed">
                  {item.why_it_failed_hypothesis}
                </p>
              </div>

              <div className="pt-2 border-t border-stone-200">
                <span className="font-bold text-stone-700 flex items-center space-x-1">
                  <Wrench className="w-3.5 h-3.5 text-sky-600" />
                  <span>Engineering Remediation (How to Fix):</span>
                </span>
                <p className="text-stone-600 mt-0.5 leading-relaxed">
                  {item.how_to_fix}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
