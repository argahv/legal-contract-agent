import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ClauseCard } from "@/components/contracts/ClauseCard";

describe("ClauseCard", () => {
  it("renders title, risk badge, and clause body", () => {
    render(
      <ClauseCard
        contractId="doc-test"
        clause={{
          id: "clause-1",
          contract_id: "c1",
          clause_type: "INDEMNITY",
          title: "Indemnity",
          body: "Party A shall indemnify Party B.",
          sequence: 1,
        }}
        risk={{
          id: "risk-1",
          clause_id: "clause-1",
          level: "HIGH",
          rationale: "Unlimited carve-outs may expand exposure.",
        }}
      />,
    );

    expect(screen.getByText("Indemnity")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(
      screen.getByText("Party A shall indemnify Party B."),
    ).toBeInTheDocument();
  });
});
