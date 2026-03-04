import { test, expect } from '@playwright/test';

test.describe('Campaign Management - CRUD Operations', () => {
  const baseURL = 'https://rbac-platform-test.preview.emergentagent.com';
  const timestamp = Date.now();
  let createdCampaignName = `TEST_E2E_Campaign_${timestamp}`;
  let createdOpportunityName = `TEST_E2E_Lead_${timestamp}`;
  
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

  test('should create a new campaign successfully', async ({ page }) => {
    // Click create campaign button
    await page.getByTestId('create-campaign-btn').click();
    await expect(page.locator('.modal-overlay')).toBeVisible();
    
    // Fill the form
    await page.getByTestId('campaign-name-input').fill(createdCampaignName);
    await page.getByTestId('campaign-desc-input').fill('Test campaign created by E2E test');
    await page.getByTestId('campaign-audience-input').fill('Test target audience');
    await page.getByTestId('campaign-script-input').fill('Hello, this is a test script');
    
    // Submit form
    await page.getByTestId('submit-campaign-btn').click();
    
    // Modal should close
    await expect(page.locator('.modal-overlay')).not.toBeVisible({ timeout: 10000 });
    
    // Campaign should appear in the list
    await expect(page.locator('.campaign-card', { hasText: createdCampaignName })).toBeVisible({ timeout: 10000 });
  });

  test('should create a new opportunity in a campaign', async ({ page }) => {
    // Click on first campaign to open Kanban
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Click add opportunity button
    await page.getByTestId('add-opportunity-btn').click();
    await expect(page.locator('.modal-overlay')).toBeVisible();
    
    // Fill opportunity form
    await page.getByTestId('opportunity-name-input').fill(createdOpportunityName);
    await page.getByTestId('opportunity-phone-input').fill('+919123456789');
    await page.getByTestId('opportunity-email-input').fill('test@e2e.com');
    await page.getByTestId('opportunity-business-input').fill('E2E Test Corp');
    await page.getByTestId('opportunity-value-input').fill('7500');
    await page.getByTestId('opportunity-notes-input').fill('Created by E2E test');
    
    // Submit form
    await page.getByTestId('submit-opportunity-btn').click();
    
    // Modal should close
    await expect(page.locator('.modal-overlay')).not.toBeVisible({ timeout: 10000 });
    
    // Opportunity should appear in Dialing column
    const dialingColumn = page.getByTestId('column-dialing');
    await expect(dialingColumn.locator('.opportunity-card', { hasText: createdOpportunityName })).toBeVisible({ timeout: 10000 });
  });

  test('should verify opportunity cards have action icons', async ({ page }) => {
    // Open a campaign
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Find an opportunity card
    const opportunityCard = page.locator('.opportunity-card').first();
    
    if (await opportunityCard.isVisible()) {
      // Check action buttons exist
      const actionsContainer = opportunityCard.locator('.card-actions');
      await expect(actionsContainer).toBeVisible();
      
      // Count action buttons - should be 6 based on design
      const actionButtons = actionsContainer.locator('.action-btn');
      const buttonCount = await actionButtons.count();
      expect(buttonCount).toBe(6); // Phone, User, Message, Calendar, Mail, Trash
    }
  });

  test('should drag and drop opportunity between stages via API verification', async ({ page, request }) => {
    // Open a campaign
    await page.locator('.campaign-card').first().click();
    await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
    
    // Get auth token from localStorage
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();
    
    // Find an opportunity in dialing column
    const dialingColumn = page.getByTestId('column-dialing');
    const firstOppCard = dialingColumn.locator('.opportunity-card').first();
    
    if (await firstOppCard.isVisible()) {
      // Get the opportunity ID from data-testid
      const testId = await firstOppCard.getAttribute('data-testid');
      const oppId = testId?.replace('opportunity-card-', '');
      
      if (oppId) {
        // Simulate drag by calling API directly (more reliable than drag-drop)
        const response = await request.put(`${baseURL}/api/opportunities/${oppId}/stage`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          data: { stage: 'store_visit' }
        });
        
        expect(response.status()).toBe(200);
        
        // Refresh the page to see updated positions
        await page.getByTestId('back-to-campaigns').click();
        await page.locator('.campaign-card').first().click();
        await expect(page.getByTestId('campaign-pipeline')).toBeVisible({ timeout: 10000 });
        
        // Verify opportunity is in new column
        const storeVisitColumn = page.getByTestId('column-store_visit');
        const movedCard = storeVisitColumn.locator(`[data-testid="opportunity-card-${oppId}"]`);
        await expect(movedCard).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
