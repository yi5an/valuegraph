/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./styles/**/*.{css}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2563EB",
        accent: "#F97316",
        positive: "#10B981",
        negative: "#EF4444",
        surface: "#0F172A",
        card: "#111827",
        muted: "#94A3B8"
      },
      screens: {
        mobile: "640px",
        tablet: "768px",
        desktop: "1024px"
      },
      boxShadow: {
        panel: "0 24px 60px rgba(15, 23, 42, 0.32)"
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 30%), radial-gradient(circle at top right, rgba(249, 115, 22, 0.12), transparent 25%)"
      }
    }
  },
  plugins: []
};
