import React, { useEffect, useState } from "react";
import { FileText, Download, Check } from "lucide-react";

export const ReportView: React.FC = () => {
  const [markdown, setMarkdown] = useState("");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch("/api/report")
      .then((res) => res.json())
      .then((data) => {
        setMarkdown(data.markdown || "");
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load report:", err);
        setLoading(false);
      });
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-8 h-8 border-4 border-stone-200 border-t-stone-900 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-xs flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-stone-900 flex items-center space-x-2">
            <FileText className="w-5 h-5 text-sky-600" />
            <span>Architecture & Benchmark Engineering Report</span>
          </h3>
          <p className="text-xs text-stone-500 mt-0.5">
            Full empirical documentation generated at <code>report/REPORT.md</code>
          </p>
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-stone-300 text-xs font-medium text-stone-700 hover:bg-stone-50 transition"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Download className="w-3.5 h-3.5 text-stone-500" />
              <span>Copy Markdown</span>
            </>
          )}
        </button>
      </div>

      <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-xs font-sans text-stone-800 space-y-4 text-sm leading-relaxed max-w-none">
        <pre className="whitespace-pre-wrap font-sans text-sm text-stone-800 leading-relaxed overflow-x-auto">
          {markdown}
        </pre>
      </div>
    </div>
  );
};
