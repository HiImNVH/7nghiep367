/** Visual positioning guide only; this does not detect people or landmarks. */
export function FramingGuide() {
  return (
    <div className="framing-guide" aria-hidden="true">
      <svg className="framing-corners" viewBox="0 0 440 270" preserveAspectRatio="none" fill="none">
        <path d="M1 33V17Q1 1 17 1H37M403 1h20q16 0 16 16v16M439 237v16q0 16-16 16h-20M37 269H17Q1 269 1 253v-16" stroke="currentColor" strokeWidth="2" />
      </svg>
    </div>
  );
}
