import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConditionsEditor } from "@/components/console/ConditionsEditor";

describe("ConditionsEditor", () => {
  it("renders conditions and calls onChange when edited", () => {
    const onChange = vi.fn();
    render(
      <ConditionsEditor
        conditions={[
          {
            id: "1",
            code: "single_pay_stub",
            title: "Second pay stub",
            rationale: "Need one more",
          },
        ]}
        onChange={onChange}
      />
    );

    expect(screen.getByDisplayValue("Second pay stub")).toBeInTheDocument();
    fireEvent.change(screen.getByDisplayValue("Second pay stub"), {
      target: { value: "Updated title" },
    });
    expect(onChange).toHaveBeenCalled();
  });
});
