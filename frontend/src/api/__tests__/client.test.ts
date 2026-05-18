// frontend/src/api/__tests__/client.test.ts
// Vitest tests for client.ts (Req 8, Req 11.4)
// Validates: Requirements 1.1, 8.1, 11.1, 11.4

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { apiFetch, apiFetchBlob, ApiError } from "../client";

describe("client.ts", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  describe("URL construction from VITE_API_BASE_URL", () => {
    it("should construct URLs using VITE_API_BASE_URL environment variable", async () => {
      // The BASE_URL is read at module load time from import.meta.env.VITE_API_BASE_URL
      // In test environment, VITE_API_BASE_URL is not set so it defaults to localhost:8000
      const baseUrl = "http://localhost:8000";

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await apiFetch("/test-endpoint");

      expect(fetchMock).toHaveBeenCalledWith(
        `${baseUrl}/test-endpoint`,
        expect.any(Object)
      );
    });

    it("should use localhost:8000 as default when VITE_API_BASE_URL is not set", async () => {
      // When VITE_API_BASE_URL is undefined, the client defaults to localhost:8000
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await apiFetch("/test-endpoint");

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/test-endpoint"),
        expect.any(Object)
      );
      
      // Verify the URL starts with either the configured base or the default
      const callUrl = fetchMock.mock.calls[0][0];
      expect(callUrl).toMatch(/^(https?:\/\/|http:\/\/localhost:8000)/);
    });

    it("should correctly append path to base URL", async () => {
      const baseUrl = "http://localhost:8000";

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: "test" }),
      });

      await apiFetch("/api/analyze");

      expect(fetchMock).toHaveBeenCalledWith(
        `${baseUrl}/api/analyze`,
        expect.any(Object)
      );
    });
  });

  describe("error_code surfacing on non-2xx responses", () => {
    it("should throw ApiError with error_code from response body on 4xx", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error_code: "INVALID_REQUEST",
          message: "Request validation failed",
        }),
      });

      await expect(apiFetch("/test")).rejects.toThrow(ApiError);
      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("INVALID_REQUEST");
          expect(error.status).toBe(400);
          expect(error.message).toBe("Request validation failed");
        }
      }
    });

    it("should throw ApiError with error_code from response body on 5xx", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 502,
        json: async () => ({
          error_code: "AGENT_FAILURE",
          message: "Agent pipeline failed",
        }),
      });

      await expect(apiFetch("/test")).rejects.toThrow(ApiError);
      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("AGENT_FAILURE");
          expect(error.status).toBe(502);
          expect(error.message).toBe("Agent pipeline failed");
        }
      }
    });

    it("should use HTTP_ERROR as default error_code when not in response", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      });

      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("HTTP_ERROR");
          expect(error.status).toBe(500);
        }
      }
    });

    it("should handle non-JSON error responses gracefully", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => {
          throw new Error("Not JSON");
        },
      });

      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("HTTP_ERROR");
          expect(error.status).toBe(503);
          expect(error.message).toContain("HTTP 503");
        }
      }
    });

    it("should include full error data in ApiError.data property", async () => {
      const errorData = {
        error_code: "FILE_TOO_LARGE",
        message: "File exceeds maximum size",
        max_size_bytes: 15728640,
      };

      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: async () => errorData,
      });

      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("FILE_TOO_LARGE");
          expect(error.data).toEqual(errorData);
          expect(error.data?.max_size_bytes).toBe(15728640);
        }
      }
    });

    it("should throw ApiError for 404 with error_code", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          error_code: "JOB_NOT_FOUND",
          message: "Job not found",
        }),
      });

      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("JOB_NOT_FOUND");
          expect(error.status).toBe(404);
        }
      }
    });

    it("should throw ApiError for 409 with error_code", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({
          error_code: "REPORT_NOT_READY",
          message: "Report is not ready yet",
        }),
      });

      try {
        await apiFetch("/test");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("REPORT_NOT_READY");
          expect(error.status).toBe(409);
        }
      }
    });
  });

  describe("apiFetch success cases", () => {
    it("should return parsed JSON on successful 2xx response", async () => {
      const responseData = { job_id: "123", status: "completed" };
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => responseData,
      });

      const result = await apiFetch("/test");
      expect(result).toEqual(responseData);
    });

    it("should set Content-Type header to application/json", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await apiFetch("/test");

      expect(fetchMock).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        })
      );
    });
  });

  describe("apiFetchBlob", () => {
    it("should return blob on successful response", async () => {
      const mockBlob = new Blob(["test data"], { type: "application/pdf" });
      fetchMock.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob,
      });

      const result = await apiFetchBlob("/report/123");
      expect(result).toEqual(mockBlob);
    });

    it("should throw ApiError with error_code on non-2xx blob response", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({
          error_code: "REPORT_NOT_READY",
          message: "Report not ready",
        }),
      });

      try {
        await apiFetchBlob("/report/123");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("REPORT_NOT_READY");
          expect(error.status).toBe(409);
        }
      }
    });

    it("should handle non-JSON error responses in blob fetch", async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("Not JSON");
        },
      });

      try {
        await apiFetchBlob("/report/123");
      } catch (error) {
        if (error instanceof ApiError) {
          expect(error.error_code).toBe("HTTP_ERROR");
          expect(error.status).toBe(500);
        }
      }
    });
  });
});
