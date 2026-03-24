import { useMutation, useQuery } from "@tanstack/react-query";
import { executeWorkflow, getWorkflowStatus } from "@/lib/api";
import type { WorkflowRequest, WorkflowStatus } from "@/lib/api";

export function useWorkflow() {
  const executeMutation = useMutation({
    mutationFn: (request: WorkflowRequest) => executeWorkflow(request),
  });

  const statusQuery = useQuery<WorkflowStatus>({
    queryKey: ["workflow-status", executeMutation.data?.id],
    queryFn: () => getWorkflowStatus(executeMutation.data!.id),
    enabled: !!executeMutation.data?.id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    },
  });

  const isRunning =
    executeMutation.isPending ||
    (!!executeMutation.data?.id &&
      (statusQuery.data?.status === "pending" || statusQuery.data?.status === "running"));

  return {
    execute: (workflowName: string, parameters: Record<string, unknown>) =>
      executeMutation.mutate({ workflow_name: workflowName, parameters }),
    workflowId: executeMutation.data?.id ?? null,
    status: statusQuery.data ?? null,
    isLoading: isRunning,
    error: executeMutation.error ?? statusQuery.error ?? null,
    result: statusQuery.data?.result ?? null,
    reset: executeMutation.reset,
  };
}
