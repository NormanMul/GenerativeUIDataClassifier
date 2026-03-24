import { useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAssets } from "@/lib/api";
import type { DataAsset, AssetColumn } from "@/lib/api";

const SOURCE_TYPES = ["PostgreSQL", "SAP", "Fabric"] as const;

function qualityBadge(score: number): string {
  if (score >= 90) return "bg-green-100 text-green-800";
  if (score >= 70) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

function ColumnDetails({ columns }: { columns: AssetColumn[] }): React.JSX.Element {
  if (columns.length === 0) {
    return <p className="px-6 py-3 text-xs text-gray-400">No column information available</p>;
  }
  return (
    <div className="overflow-x-auto bg-gray-50 px-6 py-3">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-gray-500">
            <th className="pb-1 pr-4 font-medium">Column</th>
            <th className="pb-1 pr-4 font-medium">Type</th>
            <th className="pb-1 pr-4 font-medium">Nullable</th>
            <th className="pb-1 pr-4 font-medium">Classification</th>
            <th className="pb-1 font-medium">PII</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {columns.map((col) => (
            <tr key={col.name}>
              <td className="py-1 pr-4 font-mono text-gray-800">{col.name}</td>
              <td className="py-1 pr-4 text-gray-600">{col.data_type}</td>
              <td className="py-1 pr-4 text-gray-600">{col.nullable ? "Yes" : "No"}</td>
              <td className="py-1 pr-4 text-gray-600">{col.classification ?? "—"}</td>
              <td className="py-1">
                {col.pii_detected ? (
                  <span className="rounded bg-red-100 px-1.5 py-0.5 text-red-700">PII</span>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Spinner(): React.JSX.Element {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
    </div>
  );
}

export default function DataCatalog(): React.JSX.Element {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Debounce search input
  const debounceRef = useMemo(() => {
    let timer: ReturnType<typeof setTimeout>;
    return (value: string) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        setDebouncedSearch(value);
        setPage(1);
      }, 300);
    };
  }, []);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value);
      debounceRef(e.target.value);
    },
    [debounceRef],
  );

  const toggleSource = (source: string) => {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(source)) next.delete(source);
      else next.add(source);
      return next;
    });
    setPage(1);
  };

  const queryParams = useMemo(
    () => ({
      query: debouncedSearch || undefined,
      source_type: selectedSources.size === 1 ? [...selectedSources][0] : undefined,
      page,
      page_size: pageSize,
    }),
    [debouncedSearch, selectedSources, page],
  );

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["assets", queryParams],
    queryFn: () => getAssets(queryParams),
  });

  const assets: DataAsset[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Client-side filter when multiple sources selected
  const filteredAssets =
    selectedSources.size > 1
      ? assets.filter((a) => selectedSources.has(a.source_type))
      : assets;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Data Catalog</h1>

      {/* Search bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={search}
            onChange={handleSearchChange}
            placeholder="Search data assets by name, schema, or tag…"
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        {SOURCE_TYPES.map((source) => {
          const active = selectedSources.has(source);
          return (
            <button
              key={source}
              onClick={() => toggleSource(source)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                active
                  ? "bg-blue-600 text-white"
                  : "border border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {source}
            </button>
          );
        })}
        {selectedSources.size > 0 && (
          <button
            onClick={() => setSelectedSources(new Set())}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Loading */}
      {isLoading && <Spinner />}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load assets: {(error as Error).message}
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && (
        <>
          {filteredAssets.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-white py-16 text-center">
              <svg
                className="mx-auto h-10 w-10 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                />
              </svg>
              <p className="mt-3 text-sm font-medium text-gray-500">No data assets found</p>
              <p className="mt-1 text-xs text-gray-400">
                {debouncedSearch ? "Try a different search term" : "Connect a data source to begin cataloging"}
              </p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Name
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Source
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Database
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Schema
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Quality
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Tags
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Updated
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredAssets.map((asset) => (
                    <>
                      <tr
                        key={asset.id}
                        onClick={() =>
                          setExpandedRow(expandedRow === asset.id ? null : asset.id)
                        }
                        className="cursor-pointer transition-colors hover:bg-blue-50"
                      >
                        <td className="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">
                          {asset.name}
                        </td>
                        <td className="whitespace-nowrap px-5 py-3 text-sm text-gray-600">
                          {asset.source_type}
                        </td>
                        <td className="whitespace-nowrap px-5 py-3 text-sm text-gray-600">
                          {asset.database}
                        </td>
                        <td className="whitespace-nowrap px-5 py-3 text-sm text-gray-600">
                          {asset.schema}
                        </td>
                        <td className="whitespace-nowrap px-5 py-3">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${qualityBadge(asset.quality_score)}`}
                          >
                            {asset.quality_score}%
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex flex-wrap gap-1">
                            {asset.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                              >
                                {tag}
                              </span>
                            ))}
                            {asset.tags.length > 3 && (
                              <span className="text-xs text-gray-400">
                                +{asset.tags.length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-5 py-3 text-xs text-gray-400">
                          {new Date(asset.updated_at).toLocaleDateString()}
                        </td>
                      </tr>
                      {expandedRow === asset.id && (
                        <tr key={`${asset.id}-detail`}>
                          <td colSpan={7} className="border-t border-blue-100 bg-blue-50/30">
                            <ColumnDetails columns={asset.columns} />
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-gray-500">
                Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  ← Prev
                </button>
                <span className="flex items-center text-xs text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
