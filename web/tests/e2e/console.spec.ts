import { expect, test } from "@playwright/test";

test("renders the control console shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("CheckpointAI").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByLabel("API Token")).toBeVisible();
  await expect(page.getByRole("link", { name: "Approvals" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Runs" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Shadows" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Autonomy" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
});
