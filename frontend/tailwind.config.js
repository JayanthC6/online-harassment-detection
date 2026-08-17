/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Core Surfaces ──
        bg:          "#0B0C16",      // deep space cyber purple-black
        surface:     "#131426",      // card / panel
        "surface-2": "#1A1B33",      // elevated card
        "surface-3": "#252744",      // hover / active
        border:      "#262846",      // default border
        "border-2":  "#383B61",      // accent border
        
        // ── Brand Cyber Cyan ──
        blue:        "#00F2FE",      // neon cyan
        "blue-dim":  "#00C4CE",
        "blue-muted":"#005663",
        "blue-glow": "rgba(0,242,254,0.15)",

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
        card: "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
        panel:"0 4px 16px rgba(0,0,0,0.5)",
        blue: "0 0 0 1px rgba(59,130,246,0.4)",
        "blue-lg": "0 0 24px rgba(59,130,246,0.15)",
      },
    },
  },
  plugins: [],
}
