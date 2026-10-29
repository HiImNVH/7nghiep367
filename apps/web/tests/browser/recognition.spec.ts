import { test, expect } from '@playwright/test';
import { capture, mockModel, mockPrediction } from './fixtures';

test('real camera clip → same prediction endpoint → accepted result and fixture disclosure', async ({ page }) => {
  await mockModel(page); await mockPrediction(page);
  await page.goto('/'); await capture(page);
  await page.getByRole('button', { name: 'Gửi nhận diện', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Xin chào', exact: true })).toBeFocused();
  await expect(page.getByText(/Kết quả tạo sẵn/)).toBeVisible();
  await expect(page.locator('.confidence')).toContainText('94');
  await page.screenshot({ path: 'test-results/accepted-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'test-results/accepted-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});
test('pilot rejected outcome hides suggested meaning and allows a fresh attempt', async ({ page }) => {
  await mockModel(page, 'pilot'); await mockPrediction(page, 'rejected');
  await page.goto('/'); await capture(page);
  await page.getByRole('button', { name: 'Gửi nhận diện', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Không nhận diện được', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Xin chào', exact: true })).toHaveCount(0);
  await expect(page.getByText(/Phạm vi giới hạn/)).toBeVisible();
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Nhận diện', exact: true })).toBeEnabled();
});
test('busy error and service-unavailable startup are recoverable', async ({ page }) => {
  await mockModel(page); await mockPrediction(page, 'busy');
  await page.goto('/'); await capture(page);
  await page.getByRole('button', { name: 'Gửi nhận diện', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Hệ thống đang bận');
  await expect(page.getByText('Do not show raw server messages')).toHaveCount(0);
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Nhận diện', exact: true })).toBeEnabled();
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 503, json: { code: 'MODEL_NOT_READY', message: 'not ready', requestId: '12345678-1234-4234-8234-123456789abc' } }));
  await page.reload(); await expect(page.getByRole('alert')).toContainText('Dịch vụ nhận diện chưa sẵn sàng');
  await mockModel(page);
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByText(/Kết quả tạo sẵn/)).toBeVisible();
});
