import { describe, expect, it } from "vitest";

import { parseSseDataLine } from "@/lib/api/documents";

describe("parseSseDataLine", () => {
  it("parses document processing events", () => {
    const event = parseSseDataLine(
      'data: {"document_id":1,"status":"running","stage":"parsing"}'
    );
    expect(event?.document_id).toBe(1);
    expect(event?.status).toBe("running");
    expect(event?.stage).toBe("parsing");
  });

  it("returns null for non-data lines", () => {
    expect(parseSseDataLine(": ping")).toBeNull();
  });
});
