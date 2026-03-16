import { test, expect } from '@playwright/test';

const BASE_URL = 'https://claim-ai-1.preview.emergentagent.com';

test.describe('Claim Processing Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Login as mukesh user
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');
    
    // Fill login form
    await page.locator('input').first().fill('mukesh');
    await page.locator('input').nth(1).fill('mukesh123');
    await page.getByRole('button', { name: /continue/i }).click();
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.dashboard').first()).toBeVisible();
    
    // Click on Claim Processing icon in sidebar (2nd button)
    await page.locator('.dashboard-sidebar button').nth(1).click({ force: true });
    await page.waitForLoadState('networkidle');
    
    // Wait for claim processing page
    await expect(page.getByTestId('claim-processing-page')).toBeVisible();
  });

  test('should display claim processing page with correct elements', async ({ page }) => {
    await expect(page.getByText('ICD-10 Code Extractor')).toBeVisible();
    await expect(page.getByText('Medical Claims ICD-10 Extractor')).toBeVisible();
    await expect(page.getByTestId('start-session-btn')).toBeVisible();
    await expect(page.getByTestId('new-session-btn')).toBeVisible();
    await expect(page.getByText('Extracted Codes')).toBeVisible();
  });

  test('should create a new claim session using center button', async ({ page }) => {
    // Click Start New Session button (the purple one in center)
    await page.getByRole('button', { name: /start new session/i }).click();
    
    // Wait for session to be created - chat input should appear
    await expect(page.getByTestId('chat-input')).toBeVisible();
    // Messages container should be visible
    await expect(page.getByTestId('messages-container')).toBeVisible();
    // Upload button should be visible
    await expect(page.getByTestId('upload-btn')).toBeVisible();
    // Send button should be visible
    await expect(page.getByTestId('send-btn')).toBeVisible();
  });

  test('should create session using header New Session button', async ({ page }) => {
    // Click New Session button in header
    await page.getByTestId('new-session-btn').click();
    
    // Wait for session to be created
    await expect(page.getByTestId('chat-input')).toBeVisible();
    await expect(page.getByTestId('messages-container')).toBeVisible();
  });

  test('should send chat message and receive AI-generated ICD-10 codes', async ({ page }) => {
    // Create new session
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Type a message
    await page.getByTestId('chat-input').fill('Extract codes for patient with type 2 diabetes and hypertension');
    
    // Send the message
    await page.getByTestId('send-btn').click();
    
    // Wait for AI response - codes should appear in the codes list
    // This may take a few seconds as AI processes the request
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill').first()).toBeVisible();
    
    // Verify we got some codes
    const codeCount = await page.getByTestId('codes-list').locator('.cp-code-pill').count();
    expect(codeCount).toBeGreaterThan(0);
  });

  test('should show ICD-10 code search when Add button clicked', async ({ page }) => {
    // Create new session first
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Click Add button
    await page.getByTestId('add-code-btn').click();
    
    // Verify search input appears
    await expect(page.getByTestId('code-search-input')).toBeVisible();
    
    // Type search query
    await page.getByTestId('code-search-input').fill('diabetes');
    
    // Wait for search results
    await expect(page.locator('.cp-search-results').first()).toBeVisible();
    await expect(page.locator('.cp-search-result').first()).toBeVisible();
  });

  test('should add ICD-10 code from search', async ({ page }) => {
    // Create new session
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Click Add button and search
    await page.getByTestId('add-code-btn').click();
    await page.getByTestId('code-search-input').fill('hypertension');
    await expect(page.locator('.cp-search-results').first()).toBeVisible();
    
    // Click on first result to add it
    await page.locator('.cp-search-result').first().click();
    
    // Verify code was added to the list
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill').first()).toBeVisible();
    
    // Verify the code is I10 (hypertension)
    await expect(page.locator('.cp-code-value').first()).toContainText('I10');
  });

  test('should remove code when X button clicked', async ({ page }) => {
    // Create session and add a code
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Add a code via search
    await page.getByTestId('add-code-btn').click();
    await page.getByTestId('code-search-input').fill('hypertension');
    await expect(page.locator('.cp-search-results')).toBeVisible();
    await page.locator('.cp-search-result').first().click();
    
    // Wait for code to appear
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill').first()).toBeVisible();
    
    // Click remove button on the first code
    await page.locator('.cp-code-remove').first().click();
    
    // Verify code was removed - should show "No codes extracted yet"
    await expect(page.locator('.cp-no-codes')).toBeVisible();
  });

  test('should show session history when toggle button clicked', async ({ page }) => {
    // Click history toggle button
    await page.getByTestId('toggle-history-btn').click();
    
    // Verify sidebar shows with sessions
    await expect(page.locator('.cp-sidebar.show')).toBeVisible();
    // Sessions list should be visible
    await expect(page.locator('.cp-sessions-list')).toBeVisible();
  });

  test('export button should be disabled when no codes exist', async ({ page }) => {
    // Create new session with no codes
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Verify export button is disabled
    await expect(page.getByTestId('export-btn')).toBeDisabled();
  });

  test('should enable export button when codes exist', async ({ page }) => {
    // Create session and add a code
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Add a code
    await page.getByTestId('add-code-btn').click();
    await page.getByTestId('code-search-input').fill('diabetes');
    await expect(page.locator('.cp-search-results')).toBeVisible();
    await page.locator('.cp-search-result').first().click();
    
    // Wait for code to be added
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill').first()).toBeVisible();
    
    // Verify export button is now enabled
    await expect(page.getByTestId('export-btn')).toBeEnabled();
  });

  test('should display upload button and chat interface elements', async ({ page }) => {
    // Create session
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Verify all UI elements
    await expect(page.getByTestId('upload-btn')).toBeVisible();
    await expect(page.getByTestId('send-btn')).toBeVisible();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    await expect(page.getByTestId('codes-list')).toBeVisible();
    await expect(page.getByTestId('add-code-btn')).toBeVisible();
    await expect(page.getByTestId('export-btn')).toBeVisible();
  });

  test('should persist codes after adding via search', async ({ page }) => {
    // Create session and add codes
    await page.getByRole('button', { name: /start new session/i }).click();
    await expect(page.getByTestId('chat-input')).toBeVisible();
    
    // Add first code (diabetes - E11)
    await page.getByTestId('add-code-btn').click();
    await page.getByTestId('code-search-input').fill('diabetes');
    await expect(page.locator('.cp-search-results')).toBeVisible();
    await page.locator('.cp-search-result').first().click();
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill').first()).toBeVisible();
    
    // Verify first code was added
    const firstCodeCount = await page.getByTestId('codes-list').locator('.cp-code-pill').count();
    expect(firstCodeCount).toBe(1);
    
    // Add second code (hypertension - I10) - need to wait for search to close first
    await page.getByTestId('add-code-btn').click();
    await page.getByTestId('code-search-input').fill('hypertension');
    await expect(page.locator('.cp-search-results')).toBeVisible();
    await page.locator('.cp-search-result').first().click();
    
    // Verify both codes are in the list  
    await expect(page.getByTestId('codes-list').locator('.cp-code-pill')).toHaveCount(2);
  });
});
