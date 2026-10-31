// Record real browser MediaRecorder output from a local reference video.
// This exercises codecs and timestamps. Camera hardware E2E remains a separate check.
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(new URL('../../apps/web/package.json', import.meta.url));
const { chromium } = require('playwright');
const [source, destination] = process.argv.slice(2);
if (!source || !destination) throw new Error('Usage: node ai/tests/record_browser_fixtures.mjs SOURCE.mp4 OUTPUT_DIR');
const videoUrl = `data:video/mp4;base64,${(await readFile(source)).toString('base64')}`;
await mkdir(destination, { recursive: true });
const evidence = [];
for (const channel of ['chrome', 'msedge']) {
  const browser = await chromium.launch({ channel, headless: true });
  try {
    const page = await browser.newPage();
    for (const codec of ['vp8', 'vp9']) {
      const bytes = await page.evaluate(async ({ videoUrl, codec }) => {
        const type = `video/webm;codecs=${codec}`;
        if (!MediaRecorder.isTypeSupported(type)) throw new Error(`Unsupported ${type}`);
        const video = document.createElement('video');
        video.muted = true;
        video.src = videoUrl;
        await new Promise((done, reject) => {
          video.onloadeddata = done;
          video.onerror = reject;
        });
        const canvas = document.createElement('canvas');
        canvas.width = 320;
        canvas.height = 240;
        const context = canvas.getContext('2d');
        document.body.append(video, canvas);
        context.drawImage(video, 0, 0, 320, 240);
        const stream = canvas.captureStream(0);
        const recorder = new MediaRecorder(stream, { mimeType: type });
        const chunks = [];
        recorder.ondataavailable = event => chunks.push(event.data);
        const stopped = new Promise(done => { recorder.onstop = done; });
        await video.play();
        recorder.start();
        const timer = setInterval(() => {
          context.drawImage(video, 0, 0, 320, 240);
          stream.getVideoTracks()[0].requestFrame();
        }, 1000 / 15);
        await new Promise(done => setTimeout(done, 2500));
        recorder.stop();
        await stopped;
        clearInterval(timer);
        stream.getTracks().forEach(track => track.stop());
        video.pause();
        video.remove();
        canvas.remove();
        return Array.from(new Uint8Array(await new Blob(chunks).arrayBuffer()));
      }, { videoUrl, codec });
      if (bytes.length < 1000) throw new Error('Recorder produced an empty fixture');
      const name = `${channel}-${codec}.webm`;
      await writeFile(resolve(destination, name), Buffer.from(bytes));
      evidence.push({ browser: channel, version: browser.version(), codec, name, bytes: bytes.length,
                      source: 'canvas capture of local reference video, no physical camera' });
    }
  } finally {
    await browser.close();
  }
}
await writeFile(resolve(destination, 'browser-versions.json'), JSON.stringify(evidence, null, 2));
console.log(`Recorded ${evidence.length} browser codec fixtures`);
