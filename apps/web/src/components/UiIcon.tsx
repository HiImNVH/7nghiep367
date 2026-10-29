const paths = {
  camera: <><path d="m8 5 1.5-2h5L16 5h3a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" /><circle cx="12" cy="12" r="4" /></>,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  help: <><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2m0 3h.01" /></>,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  reset: <path d="M3 10a9 9 0 1 1 1 7M3 4v6h6" />,
  shield: <><path d="M12 3 4 6v6c0 4 5 7 8 9 3-2 8-5 8-9V6Z" /><path d="m8.5 12 2.5 2.5 4.5-5" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  hand: <path d="M8 12V5a1.5 1.5 0 0 1 3 0v6-8a1.5 1.5 0 0 1 3 0v8-6a1.5 1.5 0 0 1 3 0v7-4a1.5 1.5 0 0 1 3 0v6c0 5-3 8-7 8h-1c-2.5 0-4-1-5.5-3L3 14a1.5 1.5 0 0 1 2.5-1.5L8 15" />,
};

export function UiIcon({ name }: { name: keyof typeof paths }) {
  return <svg className="ui-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
