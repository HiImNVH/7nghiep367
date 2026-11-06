import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import AdminTraining from './features/admin/AdminTraining';
import './styles.css';

createRoot(document.getElementById('root')!).render(<StrictMode>{window.location.pathname.replace(/\/+$/, '') === '/admin/train-model' ? <AdminTraining /> : <App />}</StrictMode>);
