import type { ReactElement } from "react";

type IconKey =
  | "focus"
  | "hide"
  | "history"
  | "isolate"
  | "mesh"
  | "measure"
  | "pad"
  | "part"
  | "partdesign"
  | "pocket"
  | "recompute"
  | "redo"
  | "save"
  | "sketch"
  | "sketcher"
  | "suppression"
  | "show"
  | "undo";

const ICON_PATHS: Record<IconKey, ReactElement> = {
  focus: (
    <>
      <circle cx="12" cy="12" r="5" />
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
    </>
  ),
  hide: (
    <>
      <path d="M3 12s3.5-5 9-5 9 5 9 5-3.5 5-9 5-9-5-9-5z" />
      <path d="M4 4l16 16" />
    </>
  ),
  history: (
    <>
      <path d="M5 8V4l-3 3 3 3V8h7a5 5 0 1 1-4.9 6" />
      <path d="M12 9v4l3 2" />
    </>
  ),
  isolate: (
    <>
      <path d="M4 4h6v6H4zM14 14h6v6h-6z" />
      <path d="M10 7h4M12 5v4M12 15v4M10 17h4" />
    </>
  ),
  mesh: (
    <>
      <path d="M6 7l6-3 6 3v10l-6 3-6-3z" />
      <path d="M6 7l6 3 6-3M12 10v10" />
    </>
  ),
  measure: (
    <>
      <path d="M5 16l11-11 3 3-11 11H5z" />
      <path d="M12 8l4 4" />
      <path d="M7 19h5" />
    </>
  ),
  pad: (
    <>
      <path d="M5 14h8v5H5z" />
      <path d="M9 14V6h8v13H9" />
    </>
  ),
  part: (
    <>
      <path d="M6 7l6-3 6 3v10l-6 3-6-3z" />
      <path d="M6 7l6 3 6-3" />
    </>
  ),
  partdesign: (
    <>
      <path d="M5 16h7v4H5z" />
      <path d="M9 16V6h10v14H9" />
      <path d="M6 12h4" />
    </>
  ),
  pocket: (
    <>
      <path d="M5 7h14v12H5z" />
      <path d="M9 11h6v8H9z" />
    </>
  ),
  recompute: (
    <>
      <path d="M7 8a6 6 0 0 1 10 1" />
      <path d="M17 5v4h-4" />
      <path d="M17 16a6 6 0 0 1-10-1" />
      <path d="M7 19v-4h4" />
    </>
  ),
  redo: (
    <>
      <path d="M8 7l5-4v3h3a5 5 0 1 1 0 10H9" />
    </>
  ),
  save: (
    <>
      <path d="M5 5h12l2 2v12H5z" />
      <path d="M8 5v5h7V5" />
      <path d="M8 19v-5h8v5" />
    </>
  ),
  sketch: (
    <>
      <rect x="5" y="6" width="14" height="12" rx="2" />
      <path d="M8 15l3-4 3 2 2-3" />
    </>
  ),
  sketcher: (
    <>
      <rect x="5" y="6" width="14" height="12" rx="2" />
      <path d="M8 15l3-4 3 2 2-3" />
    </>
  ),
  suppression: (
    <>
      <path d="M6 6l12 12" />
      <path d="M8 8h8v8H8z" />
    </>
  ),
  show: (
    <>
      <path d="M3 12s3.5-5 9-5 9 5 9 5-3.5 5-9 5-9-5-9-5z" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
  undo: (
    <>
      <path d="M16 7l-5-4v3H8a5 5 0 1 0 0 10h7" />
    </>
  )
};

function normalizeIcon(icon: string): IconKey | null {
  const normalized = icon.trim().toLowerCase() as IconKey;
  return normalized in ICON_PATHS ? normalized : null;
}

export function ShellIcon({ icon, title }: { icon?: string; title?: string }) {
  if (!icon) {
    return null;
  }

  const normalized = normalizeIcon(icon);
  if (!normalized) {
    return null;
  }

  return (
    <span
      aria-hidden="true"
      className="shell-icon"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: 14,
        height: 14,
        flex: "0 0 14px"
      }}
      title={title ?? icon}
    >
      <svg
        className="shell-icon-svg"
        fill="none"
        style={{ width: 14, height: 14, display: "block", stroke: "currentColor", strokeWidth: 1.8 }}
        viewBox="0 0 24 24"
      >
        {ICON_PATHS[normalized]}
      </svg>
    </span>
  );
}