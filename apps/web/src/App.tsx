import { vi } from './content/vi';
import { CameraRecorder } from './features/recognition/CameraRecorder';
import { useRecognition } from './features/recognition/useRecognition';
import { inferenceApi, type InferenceApi } from './services/inferenceApi';

export default function App({ api = inferenceApi }: { api?: InferenceApi }) {
  const recognition = useRecognition(api);
  return (
    <main className="app-shell">
      <h1 className="sr-only">{vi.title}</h1>
      <CameraRecorder recognition={recognition} />
    </main>
  );
}
