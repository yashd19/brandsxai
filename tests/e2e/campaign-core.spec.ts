import { test, expect } from '@playwright/test';

test.describe('Campaign Management - Core Flows', () => {
  const baseURL = 'https://multi-tenant-voice.preview.emergentagent.com';
  
  test.beforeEach(async ({ page }) => {
    // Remove Emergent badge if present
    await page.addInitScript(() => {
      const observer = new MutationObserver(() => {
        const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
        if (badge) badge.remove();
      });
      observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
    });
  });

  test('should login successfully as brand user', async ({ page }) => {
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    
    // Fill login credentials
    await page.getByPlaceholder('Username').fill('mukesh');
    await page.getByPlaceholder('Password').fill('mukesh123');
    
    // Click Continue button
    await page.getByRole('button', { name: 'Continue' }).click();
    
    // Wait for dashboard to load
    await expect(page.locator('.dashboard').first()).toBeVisible({ timeout: 15000 });
    
    // Verify user is logged in - check for dashboard elements
    await expect(page.locator('.sidebar-nav')).toBeVisible();
  });

  test('should navigate to Campaign tab in dashboard', async ({ page }) => {
    // Login first
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    await page.getByPlaceholder('Username').fill('mukesh');
    await page.getByPlaceholder('Password').fill('mukesh123');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.dashboard').first()).toBeVisible({ timeout: 15000 });
    
    // Click on Campaign tab
    await page.getByRole('button', { name: 'Campaign' }).click();
    
    // Wait for campaign list to load
    await expect(page.getByTestId('campaign-list').or(page.getByTestId('campaign-pipeline'))).toBeVisible({ timeout: 10000 });
  });

  test('should display campaign list with campaign cards', async ({ page }) => {
    // Login and navigate to campaign
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    await page.getByPlaceholder('Username').fill('mukesh');
    await page.getByPlaceholder('Password').fill('mukesh123');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.dashboard').first()).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Campaign' }).click();
    
    // Verify campaign list is visible
    const campaignList = page.getByTestId('campaign-list');
    await expect(campaignList).toBeVisible({ timeout: 10000 });
    
    // Verify header text
    await expect(page.getByRole('heading', { name: 'Voice AI Campaigns' })).toBeVisible();
    
    // Verify create campaign button exists
    await expect(page.getByTestId('create-campaign-btn')).toBeVisible();
    
    // Check if campaign cards exist (from seeded data)
    const campaignCards = page.locator('.campaign-card');
    const cardCount = await campaignCards.count();
    expect(cardCount).toBeGreaterThan(0);
    
    // Verify campaign card has required elements
    const firstCard = campaignCards.first();
    await expect(firstCard.locator('.campaign-card-header h3')).toBeVisible(); // Campaign name
    await expect(firstCard.locator('.status-badge')).toBeVisible(); // Status badge
    await expect(firstCard.locator('.stat-value').first()).toBeVisible(); // Stats
  });

  test('should open Create Campaign modal', async ({ page }) => {
    // Login and navigate to campaign
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    await page.getByPlaceholder('Username').fill('mukesh');
    await page.getByPlaceholder('Password').fill('mukesh123');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.dashboard').first()).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Campaign' }).click();
    await expect(page.getByTestId('campaign-list')).toBeVisible({ timeout: 10000 });
    
    // Click create campaign button
    await page.getByTestId('create-campaign-btn').click();
    
    // Verify modal is visible
    await expect(page.locator('.modal-overlay')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Campaign' })).toBeVisible();
    
    // Verify form fields exist
    await expect(page.getByTestId('campaign-name-input')).toBeVisible();
    await expect(page.getByTestId('campaign-desc-input')).toBeVisible();
    await expect(page.getByTestId('campaign-start-input')).toBeVisible();
    await expect(page.getByTestId('campaign-end-input')).toBeVisible();
    await expect(page.getByTestId('campaign-audience-input')).toBeVisible();
    await expect(page.getByTestId('campaign-script-input')).toBeVisible();
    await expect(page.getByTestId('submit-campaign-btn')).toBeVisible();
    
    // Test close modal
    await page.locator('.close-btn').click();
    await expect(page.locator('.modal-overlay')).not.toBeVisible();
  });
});
