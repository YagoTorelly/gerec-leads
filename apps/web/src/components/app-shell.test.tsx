// @vitest-environment jsdom

import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/image", () => ({
  default: () => <span />,
}));
vi.mock("../lib/auth/actions", () => ({ signOutAction: vi.fn() }));

import { AppShell } from "./app-shell";

const admin = {
  id: "admin-1",
  userId: "admin-1",
  fullName: "Yago",
  email: "yago@wtgseguros.com.br",
  role: "admin" as const,
};

const seller = { ...admin, id: "seller-1", userId: "seller-1", fullName: "Jessica", role: "seller" as const };

function renderShell(profile: typeof admin | typeof seller) {
  return render(
    <AppShell profile={profile}>
      <p>Conte\u00fado</p>
    </AppShell>,
  );
}

afterEach(cleanup);

describe("navega\u00e7\u00e3o do AppShell", () => {
  it("mostra Relat\u00f3rios somente para administrador", () => {
    expect(renderShell(admin).getByRole("link", { name: "Relat\u00f3rios" })).toBeTruthy();
    cleanup();
    expect(renderShell(seller).queryByRole("link", { name: "Relat\u00f3rios" })).toBeNull();
  });
});
