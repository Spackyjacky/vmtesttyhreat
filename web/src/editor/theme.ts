import { EditorView } from "@codemirror/view";

export const lightTheme = EditorView.theme({
  "&": { color: "#1a1a1a", backgroundColor: "#ffffff" },
  ".cm-content": { caretColor: "#1a1a1a" },
  ".cm-gutters": { backgroundColor: "#f3f3f3", color: "#888", border: "none" },
});

export const darkTheme = EditorView.theme(
  {
    "&": { color: "#d4d4d4", backgroundColor: "#1e1e1e" },
    ".cm-content": { caretColor: "#ffffff" },
    ".cm-gutters": { backgroundColor: "#252526", color: "#6e6e6e", border: "none" },
    ".cm-activeLine": { backgroundColor: "#2a2d2e" },
    ".cm-activeLineGutter": { backgroundColor: "#2a2d2e" },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": {
      backgroundColor: "#264f78 !important",
    },
    ".cm-searchMatch": { backgroundColor: "#72a1ff59" },
    ".cm-searchMatch.cm-searchMatch-selected": { backgroundColor: "#ff9632" },
  },
  { dark: true },
);
