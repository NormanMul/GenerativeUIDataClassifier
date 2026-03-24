import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPolicies, getAuditTrail, getTrustScores, getGovernanceStats } from "@/lib/api";
import type { Policy, AuditEvent, TrustScore, GovernanceStats } from "@/lib/api";

type Tab = "policies" | "audit" | "trust";

function Spinner(): React.JSX.Element {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-6 w-6 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
    </div>
  );
}

function StatsCards({ stats }: { stats: GovernanceStats | undefined }): React.JSX.Element {
  const cards = [
    {
      label: "Total Evaluations",
      value: stats?.total_evaluations?.toLocaleString() ?? "—",
      icon: "📋",
      color: "bg-blue-50 text-blue-700",
    },
    {
      label: "Approval Rate",
      value: stats ? `${(stats.approval_rate * 100).toFixed(1)}%` : "—",
      icon: "✅",
      color: "bg-green-50 text-green-700",
    },
    {
      label: "Avg Trust Score",
      value: stats?.avg_trust_score?.toFixed(0) ?? "—",
      icon: "🛡️",
      color: "bg-purple-50 text-purple-700",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span className={`rounded-lg p-2 text-lg ${card.color}`}>{card.icon}</span>
            <div>
              <p className="text-xs font-medium text-gray-500">{card.label}</p>
              <p className="text-xl font-bold text-gray-900">{card.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function PoliciesTab(): React.JSX.Element {
  const { data: policies, isLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: getPolicies,
  });

  if (isLoading) return <Spinner />;
  if (!policies || policies.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No policies configured yet.</p>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
            <th className="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Type</th>
            <th className="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Effect</th>
            <th className="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Severity</th>
            <th className="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {policies.map((policy: Policy) => (
            <tr key={policy.id} className="hover:bg-gray-50">
              <td className="px-5 py-3">
                <p className="text-sm font-medium text-gray-900">{policy.name}</p>
                <p className="mt-0.5 text-xs text-gray-500">{policy.description}</p>
              </td>
              <td className="px-5 py-3 text-sm text-gray-600">{policy.type}</td>
              <td className="px-5 py-3">
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    policy.effect === "allow"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {policy.effect}
                </span>
              </td>
              <td className="px-5 py-3">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    policy.severity === "critical"
                      ? "bg-red-100 text-red-700"
                      : policy.severity === "high"
                        ? "bg-orange-100 text-orange-700"
                        : policy.severity === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {policy.severity}
                </span>
              </td>
              <td className="px-5 py-3">
                <span
                  className={`inline-flex items-center gap-1 text-xs font-medium ${
                    policy.enabled ? "text-green-600" : "text-gray-400"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${policy.enabled ? "bg-green-500" : "bg-gray-300"}`}
                  />
                  {policy.enabled ? "Active" : "Disabled"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTab(): React.JSX.Element {
  const [page, setPage] = useState(1);
  const [decisionFilter, setDecisionFilter] = useState<string>("");
  const pageSize = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["audit", page, decisionFilter],
    queryFn: () =>
      getAuditTrail({
        page,
        page_size: pageSize,
        decision: decisionFilter || undefined,
      }),
  });

  const events: AuditEvent[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-3">
      {/* Filter */}
      <div className="flex gap-2">
        <select
          value={decisionFilter}
          onChange={(e) => {
            setDecisionFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm"
        >
          <option value="">All decisions</option>
          <option value="allow">Allow</option>
          <option value="deny">Deny</option>
        </select>
      </div>

      {isLoading ? (
        <Spinner />
      ) : events.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-400">No audit events recorded.</p>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Actor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Resource
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Decision
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {events.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-2.5 text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 text-sm text-gray-800">{event.actor}</td>
                    <td className="px-4 py-2.5 text-sm text-gray-600">{event.action}</td>
                    <td className="max-w-[200px] truncate px-4 py-2.5 text-sm text-gray-600">
                      {event.resource}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                          event.decision === "allow"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {event.decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                Page {page} of {totalPages} ({total} events)
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded border border-gray-300 bg-white px-3 py-1 text-xs disabled:opacity-40"
                >
                  ← Prev
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded border border-gray-300 bg-white px-3 py-1 text-xs disabled:opacity-40"
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

function TrustTab(): React.JSX.Element {
  const { data: scores, isLoading } = useQuery({
    queryKey: ["trust-scores"],
    queryFn: getTrustScores,
  });

  if (isLoading) return <Spinner />;
  if (!scores || scores.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No trust scores available.</p>;
  }

  const maxScore = 1000;

  return (
    <div className="space-y-3">
      {scores.map((ts: TrustScore) => {
        const pct = Math.min(100, (ts.score / maxScore) * 100);
        const color =
          ts.score >= 700 ? "bg-green-500" : ts.score >= 400 ? "bg-yellow-500" : "bg-red-500";

        return (
          <div key={ts.entity_id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{ts.entity_name}</p>
                <p className="text-xs text-gray-500">{ts.entity_type}</p>
              </div>
              <span className="text-lg font-bold text-gray-900">{ts.score}</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
              <div
                className={`h-full rounded-full transition-all duration-500 ${color}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            {ts.factors.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {ts.factors.map((f) => (
                  <span key={f.name} className="rounded bg-gray-50 px-2 py-0.5 text-xs text-gray-500">
                    {f.name}: {f.value}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function GovernanceCenter(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>("policies");

  const { data: stats } = useQuery({
    queryKey: ["governance-stats"],
    queryFn: getGovernanceStats,
  });

  const tabs: { id: Tab; label: string }[] = [
    { id: "policies", label: "Policies" },
    { id: "audit", label: "Audit Trail" },
    { id: "trust", label: "Trust Scores" },
  ];

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Governance Center</h1>

      {/* Stats cards */}
      <StatsCards stats={stats} />

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`border-b-2 pb-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === "policies" && <PoliciesTab />}
      {activeTab === "audit" && <AuditTab />}
      {activeTab === "trust" && <TrustTab />}
    </div>
  );
}
