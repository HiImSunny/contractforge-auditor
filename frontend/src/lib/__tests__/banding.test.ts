import { describe, it, expect } from "vitest";
import { band } from "../banding";

describe("banding", () => {
  describe("band()", () => {
    it("should return 'green' for score 0", () => {
      expect(band(0)).toMatchSnapshot();
    });

    it("should return 'green' for score 33", () => {
      expect(band(33)).toMatchSnapshot();
    });

    it("should return 'amber' for score 34", () => {
      expect(band(34)).toMatchSnapshot();
    });

    it("should return 'amber' for score 66", () => {
      expect(band(66)).toMatchSnapshot();
    });

    it("should return 'red' for score 67", () => {
      expect(band(67)).toMatchSnapshot();
    });

    it("should return 'red' for score 100", () => {
      expect(band(100)).toMatchSnapshot();
    });

    // Additional boundary tests for completeness
    it("should return 'green' for score 1", () => {
      expect(band(1)).toMatchSnapshot();
    });

    it("should return 'amber' for score 50", () => {
      expect(band(50)).toMatchSnapshot();
    });

    it("should return 'red' for score 99", () => {
      expect(band(99)).toMatchSnapshot();
    });
  });
});
