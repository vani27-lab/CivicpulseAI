/** Design tokens shared by the officer and citizen apps (Module 6 should reuse this file). */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Public Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        paper: '#F3F5F7',
        ink: '#17212B',
        muted: '#4F5B67',
        line: '#D3DAE1',
        civic: { DEFAULT: '#1D4E7A', dark: '#123452', soft: '#E4EEF7' },
        // Priority palette. "rail" = solid colour for bars/map, "tint"/"text" = badge background/foreground.
        high: { rail: '#C8301F', tint: '#FDECEA', text: '#9F1F12' },
        medium: { rail: '#E8710A', tint: '#FFF1E0', text: '#9A4A05' },
        low: { rail: '#2E8B57', tint: '#E6F4EA', text: '#17663A' },
      },
    },
  },
  plugins: [],
}
