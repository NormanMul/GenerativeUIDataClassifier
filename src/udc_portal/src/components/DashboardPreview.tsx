import type { DashboardSpec } from "@/lib/api";

const CHART_ICONS: Record<string, string> = {
  bar: "📊",
  line: "📈",
  pie: "🥧",
  table: "📋",
  card: "🔢",
  scatter: "⚬",
  map: "🗺️",
  gauge: "⏱️",
};

interface DashboardPreviewProps {
  spec: DashboardSpec | null;
}

export default function DashboardPreview({ spec }: DashboardPreviewProps): React.JSX.Element {
  if (!spec) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white text-sm text-gray-400">
        Dashboard preview will appear here after generation
      </div>
    );
  }

  const cols = spec.layout?.columns ?? 2;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-5 py-4">
        <h3 className="text-lg font-semibold text-gray-900">{spec.title}</h3>
        {spec.description && (
          <p className="mt-1 text-sm text-gray-500">{spec.description}</p>
        )}
      </div>

      {/* Quality warnings */}
      {spec.quality_warnings && spec.quality_warnings.length > 0 && (
        <div className="border-b border-yellow-200 bg-yellow-50 px-5 py-3">
          <p className="text-xs font-medium text-yellow-800">⚠ Quality Warnings</p>
          <ul className="mt-1 space-y-0.5">
            {spec.quality_warnings.map((w, i) => (
              <li key={i} className="text-xs text-yellow-700">
                • {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Visuals grid */}
      <div
        className="gap-4 p-5"
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
        }}
      >
        {spec.visuals.map((visual) => (
          <div
            key={visual.id}
            className="flex flex-col rounded-lg border border-gray-200 bg-gray-50 p-4"
          >
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xl">{CHART_ICONS[visual.chart_type] ?? "📊"}</span>
              <span className="text-sm font-medium text-gray-700">{visual.title}</span>
            </div>
            <div className="flex flex-1 items-center justify-center rounded border border-dashed border-gray-300 bg-white p-6 text-center text-xs text-gray-400">
              <div>
                <p className="font-medium capitalize text-gray-500">{visual.chart_type} chart</p>
                <p className="mt-1">Source: {visual.data_source}</p>
                {visual.measures.length > 0 && (
                  <p className="mt-0.5">Measures: {visual.measures.join(", ")}</p>
                )}
                {visual.dimensions.length > 0 && (
                  <p className="mt-0.5">Dimensions: {visual.dimensions.join(", ")}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-gray-200 px-5 py-3">
        <span className="text-xs text-gray-400">
          {spec.data_sources.length} data source{spec.data_sources.length !== 1 ? "s" : ""}
        </span>
        {spec.power_bi_url && (
          <a
            href={spec.power_bi_url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-yellow-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-yellow-600"
          >
            Open in Power BI
          </a>
        )}
      </div>
    </div>
  );
}
