import React from "react";
import { Bot, BarChart3, AlertTriangle, FileText, ListFilter, Activity } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  brand: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, brand }) => {
  const navItems = [
    { id: "console", label: "Live Agent Console", icon: Bot },
    { id: "metrics", label: "Evaluation & Benchmarks", icon: BarChart3 },
    { id: "samples", label: "Golden Test Set (200)", icon: ListFilter },
    { id: "failures", label: "Failure Analysis", icon: AlertTriangle },
    { id: "report", label: "Architecture Report", icon: FileText },
  ];

  return (
    <header className="bg-white border-b border-stone-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-stone-900 flex items-center justify-center text-white font-semibold text-lg shadow-sm">
              <Bot className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-stone-900 text-lg tracking-tight">
                  SupportPilot AI
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
                  @{brand}
                </span>
              </div>
              <p className="text-xs text-stone-500 hidden sm:block">
                Historically Grounded • Intent Classification • Safe Escalation
              </p>
            </div>
          </div>

          <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-tab-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? "bg-stone-900 text-white shadow-xs"
                      : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-sky-400" : "text-stone-500"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};
