import React, { useState } from "react";
import { Navbar } from "./components/Navbar";
import { LiveConsole } from "./components/LiveConsole";
import { MetricsDashboard } from "./components/MetricsDashboard";
import { GoldenSamplesView } from "./components/GoldenSamplesView";
import { FailuresView } from "./components/FailuresView";
import { ReportView } from "./components/ReportView";

export default function App() {
  const [activeTab, setActiveTab] = useState<string>("console");
  const [targetQuery, setTargetQuery] = useState<string>("");

  const handleSelectSample = (msg: string) => {
    setTargetQuery(msg);
    setActiveTab("console");
  };

  return (
    <div className="min-h-screen bg-stone-100 text-stone-900 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        brand="AppleSupport"
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "console" && (
          <LiveConsole onSelectSample={handleSelectSample} />
        )}
        {activeTab === "metrics" && <MetricsDashboard />}
        {activeTab === "samples" && (
          <GoldenSamplesView onSelectSample={handleSelectSample} />
        )}
        {activeTab === "failures" && <FailuresView />}
        {activeTab === "report" && <ReportView />}
      </main>

      <footer className="border-t border-stone-200 bg-white py-4 text-center text-xs text-stone-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Unified AI Customer Support Agent • Production Benchmark Suite
          </span>
          <span className="font-mono text-stone-400">
            AppleSupport Slice • 200 Golden Samples • Gemini 3.6 Flash
          </span>
        </div>
      </footer>
    </div>
  );
}
