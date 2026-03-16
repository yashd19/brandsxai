import { Page, expect } from '@playwright/test';

export async function waitForAppReady(page: Page) {
  await page.waitForLoadState('domcontentloaded');
}

export async function dismissToasts(page: Page) {
  await page.addLocatorHandler(
    page.locator('[data-sonner-toast], .Toastify__toast, [role="status"].toast, .MuiSnackbar-root'),
    async () => {
      const close = page.locator('[data-sonner-toast] [data-close], [data-sonner-toast] button[aria-label="Close"], .Toastify__close-button, .MuiSnackbar-root button');
      await close.first().click({ timeout: 2000 }).catch(() => {});
    },
    { times: 10, noWaitAfter: true }
  );
}

export async function checkForErrors(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const errorElements = Array.from(
      document.querySelectorAll('.error, [class*="error"], [id*="error"]')
    );
    return errorElements.map(el => el.textContent || '').filter(Boolean);
  });
}

export async function loginAsBrandUser(page: Page) {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await page.locator('input').first().fill('mukesh');
  await page.locator('input').nth(1).fill('mukesh123');
  await page.getByRole('button', { name: /continue/i }).click();
  // Wait for dashboard to load
  await page.waitForLoadState('networkidle');
  await expect(page.locator('.dashboard').first()).toBeVisible();
}

export async function navigateToCampaign(page: Page) {
  // Click on Campaign tab in the page tabs
  await page.getByRole('button', { name: /campaign/i }).click();
  // Wait for campaign list or loading to complete
  await expect(page.getByTestId('campaign-list').or(page.getByTestId('campaign-pipeline'))).toBeVisible({ timeout: 10000 });
}

export async function navigateToClaimProcessing(page: Page) {
  // Click on Claim Processing icon in sidebar (2nd button)
  await page.locator('.dashboard-sidebar button').nth(1).click({ force: true });
  await page.waitForLoadState('networkidle');
  // Wait for claim processing page to load
  await expect(page.getByTestId('claim-processing-page')).toBeVisible();
}

export async function createClaimSession(page: Page) {
  // Click start new session button
  await page.getByRole('button', { name: /start new session/i }).click();
  // Wait for chat input to appear (indicates session is active)
  await expect(page.getByTestId('chat-input')).toBeVisible();
}
