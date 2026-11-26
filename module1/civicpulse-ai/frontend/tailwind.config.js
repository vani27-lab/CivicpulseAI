/** Calm, plain look: soft grey page, white cards, one blue accent. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        page: "#F6F7F9",
        ink: "#1F2933",
        muted: "#52606D",
        line: "#D5DBE1",
        accent: { DEFAULT: "#2F6B8F", dark: "#245572", soft: "#E8F1F6" },
        good: "#2E7D4F",
        danger: { DEFAULT: "#B3382C", soft: "#FBECEA" },
      },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Noto Sans",
          "Noto Sans Devanagari",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
