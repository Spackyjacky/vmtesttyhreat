import { defineConfig } from "vite";

// GitHub Pages serves this as a project site at /vmtesttyhreat/, so built
// asset URLs need that base path. Local dev keeps serving from root.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/vmtesttyhreat/" : "/",
}));
