/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Core Surfaces (Lightened slightly per user request) ──
        bg:          "#131522",      // base background
        surface:     "rgba(25, 27, 46, 0.7)",  // card / panel (glassmorphism base)
        "surface-solid": "#191B2E",  // solid fallback
        "surface-2": "rgba(32, 35, 59, 0.75)", // elevated card
        "surface-3": "rgba(42, 45, 75, 0.8)",  // hover / active
        border:      "#2E3254",      // default border
        "border-2":  "#464A73",      // accent border
        
        // ── Brand Cyber Colors ──
        blue:        "#00F2FE",      // neon cyan
        "blue-dim":  "#00C4CE",
        "blue-muted":"#005663",
        "blue-glow": "rgba(0,242,254,0.15)",
        purple:      "#A855F7",      // secondary accent for gradients
        "purple-glow":"rgba(168,85,247,0.15)",

        // ── Semantic ──
        success:     "#10B981",
        "success-bg":"rgba(16,185,129,0.1)",
        warning:     "#F59E0B",
        "warning-bg":"rgba(245,158,11,0.1)",
        danger:      "#EF4444",
        "danger-bg": "rgba(239,68,68,0.1)",
        critical:    "#F97316",
        "critical-bg":"rgba(249,115,22,0.1)",

        // ── Text ──
        "text-primary":  "#F1F5F9",
        "text-secondary":"#94A3B8",
        "text-muted":    "#64748B",
        "text-disabled": "#334155",
      },
      fontFamily: {
        sans:  ["Inter", "system-ui", "sans-serif"],
        mono:  ["'JetBrains Mono'", "monospace"],
      },
      fontSize: {
        "2xs": ["11px", { lineHeight: "1.4", letterSpacing: "0.05em" }],
        xs:    ["12px", { lineHeight: "1.4" }],
        sm:    ["13px", { lineHeight: "1.5" }],
        base:  ["14px", { lineHeight: "1.6" }],
        md:    ["15px", { lineHeight: "1.6" }],
        lg:    ["16px", { lineHeight: "1.5", fontWeight: "600" }],
        xl:    ["20px", { lineHeight: "1.4", fontWeight: "600" }],
        "2xl": ["24px", { lineHeight: "1.3", fontWeight: "700" }],
        "3xl": ["30px", { lineHeight: "1.2", fontWeight: "700" }],
        "4xl": ["36px", { lineHeight: "1.1", fontWeight: "800" }],
      },
      borderRadius: {
        DEFAULT: "8px",
        sm:  "4px",
        md:  "8px",
        lg:  "12px",
        xl:  "16px",
        full:"9999px",
      },
      spacing: {
        sidebar: "240px",
        header:  "56px",
      },
        boxShadow: {
        card: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)",
        panel: "0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)",
        blue: "0 0 0 1px rgba(59,130,246,0.4)",
        "blue-lg": "0 0 24px rgba(59,130,246,0.15)",
        "neon": "0 0 10px rgba(0, 242, 254, 0.4), 0 0 20px rgba(0, 242, 254, 0.2)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out forwards",
        "slide-up": "slideUp 0.4s ease-out forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
        slideUp: {
          "0%": { opacity: 0, transform: "translateY(10px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(0, 242, 254, 0.2)" },
          "100%": { boxShadow: "0 0 15px rgba(0, 242, 254, 0.6)" },
        },
      },
    },
  },
  plugins: [],
}
