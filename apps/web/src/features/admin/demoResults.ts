// Reads the stored ZIP produced by the ViSign admin API.
export async function readResultZip(blob: Blob): Promise<Map<string, Blob>> {
  const bytes = new DataView(await blob.arrayBuffer());
  const files = new Map<string, Blob>();
  const decoder = new TextDecoder();
  let offset = 0;
  while (offset + 30 <= bytes.byteLength && bytes.getUint32(offset, true) === 0x04034b50) {
    const flags = bytes.getUint16(offset + 6, true);
    const method = bytes.getUint16(offset + 8, true);
    const size = bytes.getUint32(offset + 18, true);
    const nameSize = bytes.getUint16(offset + 26, true);
    const extraSize = bytes.getUint16(offset + 28, true);
    const nameStart = offset + 30;
    const start = nameStart + nameSize + extraSize;
    if ((flags & 8) || method !== 0 || start + size > bytes.byteLength) {
      throw new Error('Gói kết quả không đọc được.');
    }
    const name = decoder.decode(new Uint8Array(bytes.buffer, nameStart, nameSize));
    files.set(name, blob.slice(start, start + size, name.endsWith('.png') ? 'image/png' : ''));
    offset = start + size;
  }
  return files;
}

// Demo 2 exports fixed landmark names, numbers and enum values with no embedded commas.
export function readDemoCsv(text: string) {
  const [header = '', ...lines] = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const keys = header.split(',');
  return lines.map(line => Object.fromEntries(line.split(',').map((value, i) => [keys[i], value])));
}

export function frameName(index: number) {
  return 'frames/frame_' + String(index).padStart(5, '0') + '.png';
}

