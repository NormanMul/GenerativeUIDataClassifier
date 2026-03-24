import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { generateDashboard } from "@/lib/api";
import type { DashboardSpec, DashboardGenerateRequest } from "@/lib/api";
import DashboardPreview from "@/components/DashboardPreview";
import { getStoredRole } from "@/components/RoleSelector";

interface HistoryEntry {
  id: string;
  prompt: string;
  role: string;
  timestamp: number;
  spec: DashboardSpec | null;
}

export default function DashboardBuilder(): React.JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [role, setRole] = useState(getStoredRole);
  const [currentSpec, setCurrentSpec] = useState<DashboardSpec | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const mutation = useMutation({
    mutationFn: (req: DashboardGenerateRequest) => generateDashboard(req),
    onSuccess: (spec) => {
      setCurrentSpec(spec);
      setHistory((prev) => [
        { id: crypto.randomUUID(), prompt, role, timestamp: Date.now(), spec },
        ...prev,
      ]);
    },
  });

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    mutation.mutate({ prompt: prompt.trim(), role });
  };

  const handleHistoryClick = (entry: HistoryEntry) => {
    setCurrentSpec(entry.spec);
    setPrompt(entry.prompt);
    setRole(entry.role as typeof role);
  };

  const hasQualityWarning =
    currentSpec?.quality_warnings && currentSpec.quality_warnings.length > 0;

  return (
    <div className="flex gap-6">
      {/* Main content */}
      <div className="min-w-0 flex-1 space-y-5">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Builder</h1>

        {/* Input area */}
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <label htmlFor="nl-input" className="mb-2 block text-sm font-medium text-gray-700">
            Describe the dashboard you want to build
          </label>
          <textarea
            id="nl-input"
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder='e.g. "Show me a bar chart of data quality scores by department with a filter for date range"'
            className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />

          <div className="mt-3 flex items-center gap-3">
            {/* Role selector */}
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as typeof role)}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="Business Analyst">📊 Business Analyst</option>
              <option value="Data Engineer">⚙️ Data Engineer</option>
              <option value="Data Steward">🛡️ Data Steward</option>
            </select>

            <button
              onClick={handleGenerate}
              disabled={mutation.isPending || !prompt.trim()}
              className="flex items-center gap-2 rounded-lg bg-green-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {mutation.isPending && (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              )}
              {mutation.isPending ? "Generating…" : "Generate Dashboard"}
            </button>
          </div>

          {/* Error */}
          {mutation.isError && (
            <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {(mutation.error as Error).message}
            </div>
          )}
        </div>

        {/* Quality warning */}
        {hasQualityWarning && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3">
            <p className="text-sm font-medium text-yellow-800">
              ⚠ Some data sources have quality scores below 70%
            </p>
            <p className="mt-1 text-xs text-yellow-700">
              The generated dashboard may contain unreliable data. Review quality reports before sharing.
            </p>
          </div>
        )}

        {/* Dashboard preview */}
        <DashboardPreview spec={currentSpec} />
      </div>

      {/* History sidebar */}
      <div className="w-72 flex-shrink-0">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Recent Requests</h2>
        {history.length === 0 ? (
          <p className="text-xs text-gray-400">No dashboard requests yet</p>
        ) : (
          <div className="space-y-2">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => handleHistoryClick(entry)}
                className={`w-full rounded-lg border p-3 text-left transition-colors hover:bg-blue-50 ${
                  currentSpec === entry.spec
                    ? "border-blue-300 bg-blue-50"
                    : "border-gray-200 bg-white"
                }`}
              >
                <p className="line-clamp-2 text-sm text-gray-800">{entry.prompt}</p>
                <div className="mt-1.5 flex items-center gap-2 text-xs text-gray-400">
                  <span>{entry.role}</span>
                  <span>·</span>
                  <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
