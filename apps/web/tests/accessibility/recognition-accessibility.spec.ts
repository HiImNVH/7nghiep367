import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { capture, mockModel, mockPrediction } from '../browser/fixtures';

test('keyboard, modal focus and WCAG automated checks across key views', async ({ page }) => {
  await mockModel(page); await mockPrediction(page);
  await page.goto('/'); await expect(page.getByText(/Kết quả tạo sẵn/)).toBeVisible();
  async function audit() {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(result.violations, JSON.stringify(result.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) })))).toEqual([]);
  }
  await audit();
  const help = page.getByRole('button', { name: 'Hướng dẫn', exact: true });
  await help.focus(); await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog')).toBeVisible();
  await audit();
  for (let index = 0; index < 4; index++) {
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.querySelector('dialog')?.contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape'); await expect(help).toBeFocused();
  await capture(page); await page.getByRole('button', { name: 'Gửi nhận diện', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Xin chào', exact: true })).toBeFocused();
  await audit();
  await page.setViewportSize({ width: 390, height: 844 }); await audit();
  for (const kind of ['rejected', 'busy'] as const) {
    await page.getByRole('button', { name: 'Đặt lại', exact: true }).click();
    await mockPrediction(page, kind);
    await capture(page); await page.getByRole('button', { name: 'Gửi nhận diện', exact: true }).click();
    if (kind === 'rejected') await expect(page.getByRole('heading', { name: 'Không nhận diện được', exact: true })).toBeVisible();
    else await expect(page.getByRole('alert')).toContainText('Hệ thống đang bận');
    await audit();
  }
});
