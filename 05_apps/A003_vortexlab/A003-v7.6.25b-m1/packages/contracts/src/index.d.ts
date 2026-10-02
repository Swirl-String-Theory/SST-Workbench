export type EngineVerdict = 'PASS' | 'FAIL' | 'INFO' | 'BLOCKED';
export type ResearchVerdict = 'PASS' | 'FAIL' | 'INFO' | 'NOT_APPLICABLE';
export type BenchmarkKind = 'spec-clock' | 'decomposition' | 'holdout' | 'continuum' | 'reach';

export interface GateResult {
  id: string;
  domain: 'ENGINE' | 'RESEARCH';
  verdict: EngineVerdict | ResearchVerdict;
  label: string;
  metrics: Record<string, unknown>;
  statement?: string;
}

export interface EngineRequest<TConfig = unknown> {
  protocolVersion: string;
  requestId: string;
  kind: BenchmarkKind;
  appVersion: string;
  canonVersion: string;
  catalogManifestSha256: string;
  config: TConfig;
}

export interface EngineResponse<TPayload = unknown> {
  protocolVersion: string;
  requestId: string;
  engineVersion: string;
  engineVerdict: EngineVerdict;
  researchVerdict?: ResearchVerdict;
  gates: GateResult[];
  payload: TPayload;
  provenance: Record<string, unknown>;
}

export declare const ENGINE_PROTOCOL_VERSION: string;
export declare function assertEngineResponse(value: unknown): EngineResponse;
