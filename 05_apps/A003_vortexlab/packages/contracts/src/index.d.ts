export type EngineVerdict = 'PASS' | 'FAIL' | 'INFO' | 'BLOCKED';
export type ResearchVerdict = 'PASS' | 'FAIL' | 'INFO' | 'NOT_APPLICABLE';
export type BenchmarkKind = 'spec-clock' | 'decomposition' | 'holdout' | 'continuum' | 'reach';
export type PhysicsMethodName = 'health' | 'filament.velocity' | 'filament.rk4';

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

export interface PhysicsFilament {
  id?: string;
  carrier?: string;
  points: number[][] | Float64Array;
  circulation?: number;
  ghost?: boolean;
  source?: boolean;
}

export interface PhysicsVelocityOptions {
  liaOnly?: boolean;
  aSim?: number;
  coreDelta?: number;
  liaConstant?: number;
  coreRadius?: number;
}

export interface PhysicsRequest {
  protocolVersion: string;
  requestId: string;
  method: PhysicsMethodName;
  filaments?: PhysicsFilament[];
  dt?: number;
  options?: PhysicsVelocityOptions;
}

export interface PhysicsResponse {
  protocolVersion: string;
  requestId?: string;
  ok: boolean;
  engine: string;
  engineVersion?: string;
  isNative?: boolean;
  error?: string;
  velocity?: number[][][];
  maximumSpeed?: number;
  filaments?: PhysicsFilament[];
  maximumStageSpeed?: number;
  capabilities?: Record<string, unknown>;
  elapsedMs?: number;
}

export declare const ENGINE_PROTOCOL_VERSION: string;
export declare const PHYSICS_PROTOCOL_VERSION: string;
export declare const BenchmarkKind: Readonly<Record<string, BenchmarkKind>>;
export declare const PhysicsMethod: Readonly<Record<string, PhysicsMethodName>>;
export declare function assertEngineResponse(value: unknown): EngineResponse;
export declare function assertPhysicsRequest(value: unknown): PhysicsRequest;
export declare function assertPhysicsResponse(value: unknown): PhysicsResponse;
export declare function makePhysicsRequest(partial: Partial<PhysicsRequest> & { method: PhysicsMethodName }): PhysicsRequest;
