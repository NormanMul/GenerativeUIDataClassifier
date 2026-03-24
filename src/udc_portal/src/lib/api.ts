import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
});

api.interceptors.request.use((config) => {
  const key = localStorage.getItem("udc-api-key");
  if (key) {
    config.headers["X-API-Key"] = key;
  }
  return config;
});

// ── Shared Types ──

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetColumn {
  name: string;
  data_type: string;
  nullable: boolean;
  classification?: string;
  pii_detected?: boolean;
  description?: string;
}

export interface DataAsset {
  id: string;
  name: string;
  source_type: string;
  database: string;
  schema: string;
  quality_score: number;
  tags: string[];
  updated_at: string;
  columns: AssetColumn[];
  classification?: string;
  description?: string;
  row_count?: number;
}

export interface AssetSearchParams {
  query?: string;
  source_type?: string;
  page?: number;
  page_size?: number;
}

export interface LineageNode {
  id: string;
  label: string;
  type: string;
}

export interface LineageEdge {
  source: string;
  target: string;
  label?: string;
}

export interface LineageData {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export interface QualityCheck {
  name: string;
  passed: boolean;
  details?: string;
}

export interface QualityReport {
  score: number;
  checks: QualityCheck[];
  overall_status: "pass" | "fail";
  evaluated_at?: string;
}

export interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  domain?: string;
  owner?: string;
}

export interface Policy {
  id: string;
  name: string;
  type: string;
  description: string;
  effect: "allow" | "deny";
  severity: "low" | "medium" | "high" | "critical";
  enabled: boolean;
  conditions: Record<string, unknown>;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  decision: "allow" | "deny";
  details?: string;
}

export interface AuditTrailParams {
  page?: number;
  page_size?: number;
  actor?: string;
  action?: string;
  decision?: string;
}

export interface TrustScore {
  entity_id: string;
  entity_name: string;
  entity_type: string;
  score: number;
  factors: { name: string; value: number; weight: number }[];
}

export interface DashboardVisual {
  id: string;
  title: string;
  chart_type: string;
  data_source: string;
  measures: string[];
  dimensions: string[];
  filters?: Record<string, unknown>;
}

export interface DashboardSpec {
  title: string;
  description: string;
  visuals: DashboardVisual[];
  layout: { columns: number; rows: number };
  data_sources: string[];
  power_bi_url?: string;
  quality_warnings?: string[];
}

export interface DashboardGenerateRequest {
  prompt: string;
  role: string;
}

export interface WorkflowRequest {
  workflow_name: string;
  parameters: Record<string, unknown>;
}

export interface WorkflowStatus {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  result?: unknown;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PipelineDoc {
  id: string;
  name: string;
  description: string;
  source_count: number;
  quality_score: number;
  last_run?: string;
}

export interface ClassifyRequest {
  content: string;
  contentType?: string;
}

export interface ClassifyResponse {
  label: string;
  confidence: number;
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  sources?: string[];
}

export interface GovernanceStats {
  total_evaluations: number;
  approval_rate: number;
  avg_trust_score: number;
}

// ── API Functions ──

export async function classify(request: ClassifyRequest): Promise<ClassifyResponse> {
  const { data } = await api.post<ClassifyResponse>("/api/classify", request);
  return data;
}

export async function getAssets(params?: AssetSearchParams): Promise<PaginatedResponse<DataAsset>> {
  const { data } = await api.get<PaginatedResponse<DataAsset>>("/api/meta/assets", { params });
  return data;
}

export async function getAsset(id: string): Promise<DataAsset> {
  const { data } = await api.get<DataAsset>(`/api/meta/assets/${encodeURIComponent(id)}`);
  return data;
}

export async function searchAssets(query: string): Promise<DataAsset[]> {
  const { data } = await api.get<DataAsset[]>("/api/meta/assets/search", { params: { q: query } });
  return data;
}

export async function getLineage(assetId: string): Promise<LineageData> {
  const { data } = await api.get<LineageData>(`/api/meta/lineage/${encodeURIComponent(assetId)}`);
  return data;
}

export async function getQualityReport(assetId: string): Promise<QualityReport> {
  const { data } = await api.get<QualityReport>(`/api/meta/quality/${encodeURIComponent(assetId)}`);
  return data;
}

export async function getGlossaryTerms(): Promise<GlossaryTerm[]> {
  const { data } = await api.get<GlossaryTerm[]>("/api/meta/glossary");
  return data;
}

export async function getPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/api/policy/policies");
  return data;
}

export async function getAuditTrail(params?: AuditTrailParams): Promise<PaginatedResponse<AuditEvent>> {
  const { data } = await api.get<PaginatedResponse<AuditEvent>>("/api/policy/audit", { params });
  return data;
}

export async function getTrustScores(): Promise<TrustScore[]> {
  const { data } = await api.get<TrustScore[]>("/api/policy/trust-scores");
  return data;
}

export async function getGovernanceStats(): Promise<GovernanceStats> {
  const { data } = await api.get<GovernanceStats>("/api/policy/stats");
  return data;
}

export async function generateDashboard(request: DashboardGenerateRequest): Promise<DashboardSpec> {
  const { data } = await api.post<DashboardSpec>("/api/workflow", {
    workflow_name: "dashboard_builder",
    parameters: request,
  });
  return data;
}

export async function executeWorkflow(request: WorkflowRequest): Promise<WorkflowStatus> {
  const { data } = await api.post<WorkflowStatus>("/api/workflow", request);
  return data;
}

export async function getWorkflowStatus(id: string): Promise<WorkflowStatus> {
  const { data } = await api.get<WorkflowStatus>(`/api/workflow/${encodeURIComponent(id)}/status`);
  return data;
}

export async function getPipelines(): Promise<PipelineDoc[]> {
  const { data } = await api.get<PipelineDoc[]>("/api/meta/pipelines");
  return data;
}

export async function chat(message: string, sessionId?: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/api/chat", { message, session_id: sessionId });
  return data;
}
