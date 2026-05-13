const { test, expect } = require('@playwright/test');

test.describe('Antigravity OS Landing Page Visual & Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the local file (or a dev server if configured)
    await page.goto('file://' + require('path').resolve(__dirname, '../../docs/index.html'));
  });

  test('should have the correct document title', async ({ page }) => {
    await expect(page).toHaveTitle(/Antigravity OS — The governance kernel for AI agents/);
  });

  test('should load the main landmark', async ({ page }) => {
    const main = page.locator('main#main');
    await expect(main).toBeVisible();
  });

  test('hero section should be visible and contain key headers', async ({ page }) => {
    const heroHeader = page.locator('h1');
    await expect(heroHeader).toBeVisible();
    await expect(heroHeader).toContainText('The governance kernel for AI agents.');
  });

  test('visual regression test of the hero section', async ({ page }) => {
    // Wait for the reveal animations to settle
    await page.waitForTimeout(1000); 
    const heroSection = page.locator('.hero');
    await expect(heroSection).toHaveScreenshot('hero-section.png', { maxDiffPixelRatio: 0.05 });
  });

  test('navigation should be accessible via keyboard (focus-visible)', async ({ page }) => {
    // Press Tab to focus the first interactive element
    await page.keyboard.press('Tab');
    const skipLink = page.locator('.skip-link');
    await expect(skipLink).toBeFocused();
    
    await page.keyboard.press('Tab');
    const brandLink = page.locator('.brand');
    await expect(brandLink).toBeFocused();
  });
});
