import { expect, type Page } from '@playwright/test';
import { model, accepted } from '../fixtures/inference';

export async function mockModel(page: Page, artifactKind: 'fixture' | 'pilot' | 'full' = 'fixture') {
  await page.route('**/api/v1/model-info', route => route.fulfill({ json: { ...model, artifactKind } }));
}
export async function capture(page: Page) {
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Bắt đầu quay' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Nhận diện', exact: true }).click();
  await page.waitForTimeout(500); // Collect actual MediaRecorder frames from the fake device.
  await page.getByRole('button', { name: 'Kết thúc', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Gửi nhận diện', exact: true })).toBeVisible();
}
export async function mockPrediction(page: Page, kind: 'accepted' | 'rejected' | 'busy' = 'accepted') {
  await page.route('**/api/v1/predictions', async route => {
    const request = route.request();
    const id = request.headers()['x-request-id']!;
    expect(id).toMatch(/^[\da-f-]{36}$/i);
    expect(request.headers()['content-type']).toContain('multipart/form-data; boundary=');
    const bytes = request.postDataBuffer();
    expect(bytes?.includes(Buffer.from([0x1a, 0x45, 0xdf, 0xa3]))).toBe(true);
    const result = kind === 'busy'
      ? { code: 'SERVICE_BUSY', message: 'Do not show raw server messages', requestId: id }
      : { ...accepted, requestId: id, accepted: kind === 'accepted', classLabel: kind === 'accepted' ? 'hello' : null };
    await route.fulfill({ status: kind === 'busy' ? 503 : 200, json: result, headers: { 'X-Request-ID': id, 'Retry-After': '1' } });
  });
}
