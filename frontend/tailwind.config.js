/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cool paper, not warm cream -- this is a document tool, not a
        // lifestyle brand. Ink is near-navy, never pure black.
        paper: "#F6F6F3",
        surface: "#FFFFFF",
        ink: "#14213D",
        muted: "#5B6472",
        rule: "#DBDCE0",
        // "Filed" blue: a precise, restrained accent -- evokes a filing
        // stamp or case-file tab, not a marketing gradient.
        filed: "#2451B3",
        "filed-soft": "#EAEFFB",
        // Severity colors are FUNCTIONAL ONLY (risk flags), never decorative.
        "flag-high": "#B3261E",
        "flag-high-soft": "#FBEAE9",
        "flag-mid": "#966300",
        "flag-mid-soft": "#FBF2E1",
        "flag-clear": "#2E7D4F",
        "flag-clear-soft": "#E9F5EE",
      },
      fontFamily: {
        display: ["var(--font-source-serif)", "Georgia", "serif"],
        sans: ["var(--font-plex-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
