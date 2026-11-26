/** Modern Industrial Editorial Design Theme for CivicPulse AI */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        page: "#F4F0E9",
        paper: "#FFFFFF",
        ink: "#1A1615",
        muted: "#665C59",
        line: "#DDD6CA",
        burgundy: {
          DEFAULT: "#782F32",
          dark: "#541F22",
          light: "#9A4044",
          soft: "#F6ECED",
        },
        accent: {
          DEFAULT: "#782F32",
          dark: "#541F22",
          soft: "#F6ECED",
        },
        civic: {
          DEFAULT: "#782F32",
          dark: "#541F22",
          soft: "#F6ECED",
        },
        good: "#266B46",
        danger: {
          DEFAULT: "#A3292C",
          soft: "#FBEDEE",
        },
        // Priority system colors
        high: { rail: "#A3292C", tint: "#FBEDEE", text: "#781C1E" },
        medium: { rail: "#BD681E", tint: "#FDF2E8", text: "#8A480E" },
        low: { rail: "#266B46", tint: "#ECF5F0", text: "#17482D" },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'Cambria', 'serif'],
        sans: [
          '"Inter"',
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Noto Sans",
          "Noto Sans Devanagari",
          "sans-serif",
        ],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        editorial: "0 1px 3px rgba(26, 22, 21, 0.06), 0 1px 2px rgba(26, 22, 21, 0.04)",
        card: "0 2px 8px -2px rgba(26, 22, 21, 0.08), 0 1px 4px -1px rgba(26, 22, 21, 0.04)",
        lift: "0 10px 25px -5px rgba(120, 47, 50, 0.12), 0 8px 10px -6px rgba(26, 22, 21, 0.06)",
      },
    },
  },
  plugins: [],
};
