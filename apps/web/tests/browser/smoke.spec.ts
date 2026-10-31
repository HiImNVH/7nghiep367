import { test, expect } from '@playwright/test';
import { mockModel } from './fixtures';

test('smoke: opens the app and camera preview without uploading a clip', async ({ page }) => {
  // Keep this quick UI check independent of the OS/Edge fake camera driver.
  // The existing recognition browser suite exercises getUserMedia/MediaRecorder.
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Canvas unavailable for smoke camera');
      const stream = canvas.captureStream(30);
      const draw = () => {
        context.fillStyle = '#16765b';
        context.fillRect(0, 0, canvas.width, canvas.height);
        if (stream.active) requestAnimationFrame(draw);
      };
      draw();
      return stream;
    };
  });
  await mockModel(page);
  const uploads: string[] = [];
  await page.route('**/api/v1/predictions', route => {
    uploads.push(route.request().url());
    return route.abort();
  });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Nhận diện ngôn ngữ ký hiệu Việt Nam' })).toBeAttached();
  await expect(page.getByText(/Kết quả tạo sẵn/)).toBeVisible();
  await page.getByRole('button', { name: 'Bật camera', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Nhận diện', exact: true })).toBeEnabled();
  await expect.poll(() => page.locator('video').evaluate((video: HTMLVideoElement) => video.readyState)).toBeGreaterThanOrEqual(2);
  await expect(page.getByRole('button', { name: 'Gửi nhận diện', exact: true })).toHaveCount(0);
  expect(uploads).toEqual([]);
});

test('smoke: unavailable backend shows connectivity guidance and recovers on retry', async ({ page }) => {
  await page.route('**/api/v1/model-info', route => route.fulfill({ status: 502, contentType: 'text/plain', body: '' }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Không kết nối được dịch vụ');
  await expect(page.getByRole('alert')).toContainText('Dịch vụ nhận diện chưa chạy');
  await expect(page.getByText('Không đọc được kết quả từ dịch vụ', { exact: true })).toHaveCount(0);
  await mockModel(page);
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByText(/Kết quả tạo sẵn/)).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});
