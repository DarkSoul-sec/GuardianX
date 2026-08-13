import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import DataTable from "@/shared/components/DataTable";
import type { Column } from "@/shared/components/DataTable";

interface Row {
  id: number;
  name: string;
}

const columns: Column<Row>[] = [
  { key: "id", title: "ID" },
  { key: "name", title: "Name" },
];

const rows: Row[] = [
  { id: 1, name: "Alpha" },
  { id: 2, name: "Beta" },
];

describe("DataTable", () => {
  it("renders headers with scope and an sr-only caption", () => {
    render(<DataTable columns={columns} data={rows} rowKey={(r) => r.id} />);
    const table = screen.getByRole("table", { name: "Data table" });
    expect(table).toBeInTheDocument();
    const header = screen.getByRole("columnheader", { name: "ID" });
    expect(header).toHaveAttribute("scope", "col");
  });

  it("renders a custom accessible label", () => {
    render(
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(r) => r.id}
        ariaLabel="Asset table"
      />
    );
    expect(screen.getByRole("table", { name: "Asset table" })).toBeInTheDocument();
  });

  it("renders loading skeletons instead of rows", () => {
    const { container } = render(
      <DataTable columns={columns} data={rows} loading rowKey={(r) => r.id} />
    );
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(
      container.querySelector('[aria-hidden="true"]')
    ).toBeInTheDocument();
  });

  it("renders an empty state when there is no data", () => {
    render(<DataTable columns={columns} data={[]} rowKey={(r) => r.id} />);
    expect(screen.getByText("No data available.")).toBeInTheDocument();
  });

  it("calls onRowClick when an interactive row is clicked", async () => {
    const user = userEvent.setup();
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(r) => r.id}
        onRowClick={onRowClick}
      />
    );

    await user.click(screen.getByText("Alpha"));
    expect(onRowClick).toHaveBeenCalledWith(rows[0]);
  });

  it("supports opening a row with the keyboard", async () => {
    const user = userEvent.setup();
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(r) => r.id}
        onRowClick={onRowClick}
      />
    );

    await user.tab();
    const row = screen.getByText("Alpha").closest("tr")!;
    expect(row).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onRowClick).toHaveBeenCalledWith(rows[0]);
  });
});
