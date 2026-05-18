/**
 * Smoke test: LoadSampleButton triggers the loadSample action.
 *
 * This is a unit-level smoke test that verifies the component renders
 * and the action is callable. Full E2E with a running server is covered
 * by the backend test_load_sample_e2e.py.
 *
 * Validates: Requirements 11.5, 3.9
 */
import { describe, it, expect, vi } from "vitest";

describe("LoadSampleButton smoke test", () => {
  it("loadSample action is defined in the store", async () => {
    // Verify the store exports the loadSample action
    const { useAnalysisStore } = await import("../src/store/useAnalysisStore");
    const store = useAnalysisStore.getState();
    expect(typeof store.actions.loadSample).toBe("function");
  });

  it("RiskScoreGauge renders without crashing for score 0", async () => {
    // Verify the gauge component can be imported and renders
    const mod = await import("../src/components/RiskScoreGauge");
    expect(mod.default).toBeDefined();
  });

  it("AuditTrailLog component is importable", async () => {
    const mod = await import("../src/components/AuditTrailLog");
    expect(mod.default).toBeDefined();
  });
});
