import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPipelines, getLineage, getQualityReport } from "@/lib/api";
import type { PipelineDoc } from "@/lib/api";
import LineageGraph from "@/components/LineageGraph";
import type { LineageNode as GraphNode } from "@/components/LineageGraph";
import QualityScoreCard from "@/components/QualityScoreCard";
import { useWorkflow } from "@/hooks/useWorkflow";

function Spinner(): React.JSX.Element {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-6 w-6 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
    </div>
  );
}

export default function PipelineExplorer(): React.JSX.Element {
  const [selectedPipelineId, setSelectedPipelineId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const workflow = useWorkflow();

  // Fetch pipeline list
  const pipelinesQuery = useQuery({
    queryKey: ["pipelines"],
    queryFn: getPipelines,
  });

  const pipelines: PipelineDoc[] = pipelinesQuery.data ?? [];

  // Fetch lineage for selected pipeline
  const lineageQuery = useQuery({
    queryKey: ["lineage", selectedPipelineId],
    queryFn: () => getLineage(selectedPipelineId!),
    enabled: !!selectedPipelineId,
  });

  // Fetch quality for selected pipeline
  const qualityQuery = useQuery({
    queryKey: ["quality", selectedPipelineId],
    queryFn: () => getQualityReport(selectedPipelineId!),
    enabled: !!selectedPipelineId,
  });

  const handleDocumentPipeline = () => {
    if (!selectedPipelineId) return;
    workflow.execute("pipeline_documentation", { pipeline_id: selectedPipelineId });
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline Explorer</h1>
        <button
          onClick={handleDocumentPipeline}
          disabled={!selectedPipelineId || workflow.isLoading}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {workflow.isLoading && (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          )}
          Document Pipeline
        </button>
      </div>

      {/* Workflow status */}
      {workflow.status && (
        <div
          className={`rounded-md px-4 py-2 text-sm ${
            workflow.status.status === "completed"
              ? "bg-green-50 text-green-700"
              : workflow.status.status === "failed"
                ? "bg-red-50 text-red-700"
                : "bg-blue-50 text-blue-700"
          }`}
        >
          Pipeline documentation: {workflow.status.status}
          {workflow.status.error && <span> — {workflow.status.error}</span>}
        </div>
      )}

      <div className="grid grid-cols-12 gap-5">
        {/* Left: Pipeline list */}
        <div className="col-span-3 rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-700">Pipelines</h2>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {pipelinesQuery.isLoading && <Spinner />}
            {pipelines.length === 0 && !pipelinesQuery.isLoading && (
              <p className="px-4 py-6 text-center text-xs text-gray-400">No pipelines found</p>
            )}
            {pipelines.map((pipeline) => (
              <button
                key={pipeline.id}
                onClick={() => {
                  setSelectedPipelineId(pipeline.id);
                  setSelectedNode(null);
                }}
                className={`w-full border-b border-gray-100 px-4 py-3 text-left transition-colors hover:bg-blue-50 ${
                  selectedPipelineId === pipeline.id ? "bg-blue-50" : ""
                }`}
              >
                <p className="text-sm font-medium text-gray-800">{pipeline.name}</p>
                <p className="mt-0.5 line-clamp-2 text-xs text-gray-500">{pipeline.description}</p>
                <div className="mt-1.5 flex items-center gap-3 text-xs text-gray-400">
                  <span>{pipeline.source_count} sources</span>
                  <span
                    className={`rounded-full px-1.5 py-0.5 font-medium ${
                      pipeline.quality_score >= 70
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    Q: {pipeline.quality_score}%
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center: Lineage graph */}
        <div className="col-span-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Data Lineage</h2>
          {!selectedPipelineId ? (
            <div className="flex h-80 items-center justify-center text-sm text-gray-400">
              Select a pipeline to view lineage
            </div>
          ) : lineageQuery.isLoading ? (
            <Spinner />
          ) : lineageQuery.data ? (
            <LineageGraph
              data={lineageQuery.data}
              onNodeSelect={setSelectedNode}
              height={400}
            />
          ) : (
            <div className="flex h-80 items-center justify-center text-sm text-gray-400">
              No lineage data available
            </div>
          )}
        </div>

        {/* Right: Node details */}
        <div className="col-span-3 space-y-4">
          {/* Selected node info */}
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">Node Details</h2>
            {selectedNode ? (
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-xs font-medium uppercase text-gray-400">Name</span>
                  <p className="text-gray-800">{selectedNode.label}</p>
                </div>
                <div>
                  <span className="text-xs font-medium uppercase text-gray-400">Type</span>
                  <p className="capitalize text-gray-800">{selectedNode.type ?? "Unknown"}</p>
                </div>
                <div>
                  <span className="text-xs font-medium uppercase text-gray-400">ID</span>
                  <p className="break-all font-mono text-xs text-gray-600">{selectedNode.id}</p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-400">Click a node in the graph to view details</p>
            )}
          </div>

          {/* Quality scorecard */}
          {selectedPipelineId && (
            <div>
              <h2 className="mb-2 text-sm font-semibold text-gray-700">Quality Scorecard</h2>
              {qualityQuery.isLoading ? (
                <Spinner />
              ) : qualityQuery.data ? (
                <QualityScoreCard
                  score={qualityQuery.data.score}
                  checks={qualityQuery.data.checks}
                  overallStatus={qualityQuery.data.overall_status}
                />
              ) : (
                <p className="text-xs text-gray-400">No quality data</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
