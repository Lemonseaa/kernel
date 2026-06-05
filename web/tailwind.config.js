/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "#d7dde8",
        panel: "#f8fafc",
        ink: "#0f172a",
        muted: "#64748b",
        accent: "#2563eb"
      },
      boxShadow: {
        surface: "0 1px 2px rgba(15, 23, 42, 0.06)"
      }
    }
  },
  plugins: []
};
