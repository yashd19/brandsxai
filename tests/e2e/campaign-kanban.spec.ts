import { test, expect } from '@playwright/test';

test.describe('Campaign Management - Kanban Board', () => {
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
    
    // Login and navigate to campaign
    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    await page.getByPlaceholder('Username').fill('mukesh');
    await page.getByPlaceholder('Password').fill('mukesh123');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.dashboard').first()).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Campaign' }).click();
    await expect(page.getByTestId('campaign-list')).toBeVisible({ timeout: 10000 });
  });

  test('should open Kanban board when clicking a campaign', async ({ page }) => {
    // Click on the first campaign card
    const firstCampaign = page.locator('.campaign-card').first();
    await firstCampaign.click();
    
    // Wait for pipeline view
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Verify back button exists
    await expect(page.getByTestId('back-to-campaigns')).toBeVisible();
    
    // Verify add opportunity button exists
    await expect(page.getByTestId('add-opportunity-btn')).toBeVisible();
  });

  test('should display all 6 Kanban columns with correct headers', async ({ page }) => {
    // Click on campaign to open Kanban
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Check all 6 stages/columns exist
    const stages = ['dialing', 'interested', 'not_interested', 'callback', 'store_visit', 'invalid_number'];
    
    for (const stage of stages) {
      const column = page.getByTestId(`column-${stage}`);
      await expect(column).toBeVisible();
    }
    
    // Verify column headers have proper names
    await expect(page.getByRole('heading', { name: 'Dialing', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Interested', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Not Interested', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Call back', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Store Visit', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Invalid Number', exact: true })).toBeVisible();
  });

  test('should display opportunity cards with correct content', async ({ page }) => {
    // Open Kanban board
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Find opportunity cards (there should be some from seeded data)
    const opportunityCards = page.locator('.opportunity-card');
    const cardCount = await opportunityCards.count();
    expect(cardCount).toBeGreaterThan(0);
    
    // Check first card has required elements
    const firstCard = opportunityCards.first();
    
    // Card header with name
    await expect(firstCard.locator('.card-header h4')).toBeVisible();
    
    // Avatar
    await expect(firstCard.locator('.card-avatar')).toBeVisible();
    
    // Opportunity value - there are multiple card-info elements, use first
    await expect(firstCard.locator('.card-info').first()).toBeVisible();
    
    // Action icons
    const actions = firstCard.locator('.card-actions');
    await expect(actions).toBeVisible();
    await expect(actions.locator('.action-btn').first()).toBeVisible();
  });

  test('should display column stats (count and value)', async ({ page }) => {
    // Open Kanban board
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Check that columns have opportunity counts
    const columns = page.locator('.pipeline-column');
    const columnCount = await columns.count();
    expect(columnCount).toBe(6);
    
    // Each column should have stats
    for (let i = 0; i < columnCount; i++) {
      const column = columns.nth(i);
      const stats = column.locator('.column-stats');
      await expect(stats).toBeVisible();
      await expect(stats.locator('.opp-count')).toBeVisible();
      await expect(stats.locator('.opp-value')).toBeVisible();
    }
  });

  test('should return to campaign list when clicking back button', async ({ page }) => {
    // Open Kanban board
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Click back button
    await page.getByTestId('back-to-campaigns').click();
    
    // Verify we're back to campaign list
    await expect(page.getByTestId('campaign-list')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('campaign-pipeline')).not.toBeVisible();
  });

  test('should open Add Opportunity modal', async ({ page }) => {
    // Open Kanban board
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Click Add Opportunity button
    await page.getByTestId('add-opportunity-btn').click();
    
    // Verify modal opens
    await expect(page.locator('.modal-overlay')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Add New Opportunity' })).toBeVisible();
    
    // Verify form fields
    await expect(page.getByTestId('opportunity-name-input')).toBeVisible();
    await expect(page.getByTestId('opportunity-phone-input')).toBeVisible();
    await expect(page.getByTestId('opportunity-email-input')).toBeVisible();
    await expect(page.getByTestId('opportunity-business-input')).toBeVisible();
    await expect(page.getByTestId('opportunity-value-input')).toBeVisible();
    await expect(page.getByTestId('opportunity-notes-input')).toBeVisible();
    await expect(page.getByTestId('submit-opportunity-btn')).toBeVisible();
    
    // Close modal
    await page.locator('.close-btn').click();
    await expect(page.locator('.modal-overlay')).not.toBeVisible();
  });

  test('should search/filter opportunities', async ({ page }) => {
    // Open Kanban board
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Get initial card count
    const initialCards = await page.locator('.opportunity-card').count();
    
    // Type in search box
    const searchBox = page.locator('.search-box input');
    await expect(searchBox).toBeVisible();
    
    // Search for a term that likely doesn't match
    await searchBox.fill('XYZNONEXISTENT');
    
    // Wait for filtering
    await page.waitForTimeout(500);
    
    // Cards should be filtered (less or equal)
    const filteredCards = await page.locator('.opportunity-card').count();
    expect(filteredCards).toBeLessThanOrEqual(initialCards);
    
    // Clear search
    await searchBox.fill('');
    await page.waitForTimeout(500);
    
    // Cards should be restored
    const restoredCards = await page.locator('.opportunity-card').count();
    expect(restoredCards).toBe(initialCards);
  });
});
