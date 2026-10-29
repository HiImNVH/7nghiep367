import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RecognitionResult } from '../../src/features/recognition/RecognitionResult';
import { ModelNotice } from '../../src/features/recognition/ModelNotice';
import { accepted, model } from '../fixtures/inference';

describe('Accepted / rejected result and artifact scope (T031 / T042 / T051)', () => {
  it('shows Vietnamese text, confidence and disclaimer for an accepted response', () => {
    render(<RecognitionResult result={accepted} onRetry={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Xin chào' })).toBeVisible();
    expect(screen.getByText(/94/)).toBeVisible();
    expect(screen.getByText(/không thay thế phiên dịch viên/)).toBeVisible();
  });
  it('never presents the suggested text as confirmed when rejected, even with high confidence', () => {
    render(<RecognitionResult result={{ ...accepted, text: 'Từ không được khẳng định', accepted: false, confidence: 0.99, classLabel: null }} onRetry={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Không nhận diện được' })).toBeVisible();
    expect(screen.queryByText('Từ không được khẳng định')).not.toBeInTheDocument();
  });
  it.each(['fixture', 'pilot'] as const)('discloses %s even when demoReady is contradictory', (artifactKind) => {
    render(<ModelNotice model={{ ...model, artifactKind, demoReady: true }} />);
    expect(screen.getByText(artifactKind === 'fixture' ? /Kết quả tạo sẵn/ : /Phạm vi giới hạn/)).toBeVisible();
    expect(screen.queryByText('Sẵn sàng demo MVP')).not.toBeInTheDocument();
  });
  it('keeps a full model with false readiness marked as unready', () => {
    render(<ModelNotice model={{ ...model, artifactKind: 'full' }} />);
    expect(screen.getByText(/Chưa sẵn sàng demo/)).toBeVisible();
  });
  it('only displays full readiness when the published quality metadata also meets the gates', () => {
    const meanings = Array.from({ length: 10 }, (_, index) => `Ý nghĩa ${index}`);
    render(<ModelNotice model={{ ...model, meanings, artifactKind: 'full', demoReady: true, macroF1: 0.85, perMeaningRecall: Object.fromEntries(meanings.map(m => [m, 0.7])) }} />);
    expect(screen.getByText('Sẵn sàng demo MVP')).toBeVisible();
  });
  it('does not show missing nullable fixture metrics as zero', async () => {
    render(<ModelNotice model={model} />);
    expect(screen.getByText('Chưa đánh giá')).toBeInTheDocument();
    expect(screen.queryByText('0.0%')).not.toBeInTheDocument();
  });
});
