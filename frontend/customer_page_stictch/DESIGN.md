---
name: Luminous Insurtech
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#434655'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#1d4ed8'
  on-secondary: '#ffffff'
  secondary-container: '#4069f2'
  on-secondary-container: '#fffbff'
  tertiary: '#4338d9'
  on-tertiary: '#ffffff'
  tertiary-container: '#5d55f3'
  on-tertiary-container: '#f2eeff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#dce1ff'
  secondary-fixed-dim: '#b7c4ff'
  on-secondary-fixed: '#001551'
  on-secondary-fixed-variant: '#0039b5'
  tertiary-fixed: '#e2dfff'
  tertiary-fixed-dim: '#c3c0ff'
  on-tertiary-fixed: '#0f0069'
  on-tertiary-fixed-variant: '#3323cc'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system embodies high-assurance fintech and insurtech infrastructure with an airy, precision-engineered aesthetic. Built for enterprise fraud mitigation, risk operations, and voice biometric verification, the visual style combines corporate authority with crystalline clarity.

The visual direction draws from **modern luminous minimalism** and **refined glassmorphism**:
- **Atmospheric Luminosity:** Crisp ice-blue gradients and luminous off-white planes replace heavy corporate grays, radiating security, transparency, and modern operational velocity.
- **Micro-Precision Structural Layers:** High-contrast navy typography balances against frosted, translucent surfaces and hair-line border definitions (`rgba(219, 234, 254, 0.7)`).
- **Voice & Biometric Trust:** Dedicated visual patterns for acoustic telemetry, voiceprint matching confidence scores, and real-time audio waveforms that feel scientific yet accessible.

## Colors

The palette is engineered around luminous cobalt blues, deep slate typography, and crystalline canvas fills.

### Palette Architecture
- **Primary Accent (`#2563EB`):** High-trust cobalt blue for primary action anchors, active verification states, and focused interactive elements.
- **Secondary Accent (`#1D4ED8`):** Deep royal blue for high-contrast interactive states, hover triggers, and emphasized metrics.
- **Tertiary Accent (`#4F46E5`):** Subtle indigo/lavender tone used for voiceprint telemetry, waveform spectrums, and AI processing chips.
- **Neutral Foreground (`#0F172A`):** Deep obsidian slate for optical-grade readability on light canvases. Secondary text falls back to `#475569`.
- **Canvas & Surface System:**
  - Base Canvas: Linear gradient from `#EBF3FC` (top) to `#F8FAFC` and `#FFFFFF` (bottom).
  - Elevated Cards: `#FFFFFF` with micro-borders (`#DBEAFE` at 60–80% opacity).
  - Frosted Sub-panels: `rgba(255, 255, 255, 0.75)` with a 16px background blur.
  - Verified Success: `#10B981` (emerald tone for verified audio streams).
  - Risk / Anomaly Alert: `#EF4444` (crimson tone for spoofing detection and failed matching).

## Typography

Typographic scale is constructed using Plus Jakarta Sans for its modern geometric balance, rounded letterforms, and authoritative clarity in dense data tables.

- **Headlines:** Display weights feature tight negative letter-spacing (`-0.02em` to `-0.03em`) to anchor dashboards and verification stats with high punch and presence.
- **Data & Telemetry:** Body text prioritizes optical legibility at 12px and 14px sizes. Numbers in voice confidence percentages and policy limits render with uniform tabular spacing.
- **Labels & Badges:** Micro-labels use medium-to-bold weights with slight letter tracking (`+0.02em` to `+0.04em`) to maintain sharp contrast inside pills and status chips.

## Layout & Spacing

The design system implements a 12-column responsive fluid grid structured inside a maximum content width of 1440px.

### Form-Factor Specifications
- **Desktop (≥1024px):** 12-column layout, 24px (`1.5rem`) gutter, 32px (`2rem`) canvas margin. Cards conform to multi-column analytical panels.
- **Tablet (768px - 1023px):** 8-column layout, 16px (`1rem`) gutter, 24px (`1.5rem`) outer margin. Dashboard summaries collapse into 2-by-2 modular clusters.
- **Mobile (<768px):** 4-column layout, 12px (`0.75rem`) gutter, 16px (`1rem`) outer margin. Data tables switch to vertical card lists, and audio inspection widgets stack sequentially.

### Spacing Philosophy
Rhythm is derived from a strict 4px/8px incremental base. Internal card padding is standardized at `space-lg` (24px) for desktop analytics, reducing to `space-md` (16px) on mobile viewports.

## Elevation & Depth

Visual hierarchy rejects harsh, opaque drop shadows in favor of ambient multi-stop luminous depth and frosted structural layers.

- **Level 0 (Base Canvas):** Subtle gradient plane starting from soft glacial ice (`#EBF3FC`) and cascading down to luminous porcelain white (`#FFFFFF`).
- **Level 1 (Crisp Surface Cards):** Pure white fill (`#FFFFFF`) framed by a micro-border of `1px solid rgba(219, 234, 254, 0.7)` and a diffuse ambient shadow:
  `box-shadow: 0 4px 20px -2px rgba(37, 99, 235, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)`.
- **Level 2 (Active & Floating Panes):** Translucent frosted layer:
  `background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.8)`.
  Ambient drop shadow: `0 12px 32px -4px rgba(37, 99, 235, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04)`.
- **Level 3 (Modals, Biometric Popovers & Flyouts):** High-definition glass:
  `background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(24px); box-shadow: 0 24px 48px -8px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(219, 234, 254, 0.8)`.

## Shapes

The interface embraces a modern, rounded visual geometry (`roundedness: 2` base) that softens enterprise density while maintaining architectural precision.

- **Standard Containers & Cards:** `1rem` (16px) border-radius creates smooth, friendly contours that isolate information neatly.
- **Modals & Hero Visual Frames:** `1.5rem` (24px) border-radius provides gentle framing for core telemetry displays.
- **Buttons, Badges & Segmented Controls:** Pill-shaped `9999px` radius ensures maximum tactile clarity for interaction anchors and operational switches.

## Components

### Buttons
- **Primary Action:** Solid cobalt blue (`#2563EB`) fill, text in `#FFFFFF`, fully rounded pill (`rounded-full`), padded `10px 24px`. Micro-hover: shift to `#1D4ED8` with a subtle blue glow (`box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3)`).
- **Secondary / Ghost Action:** Transparent or white fill, 1px border (`#DBEAFE`), navy text (`#0F172A`). Hover state induces a frosted tint (`#F0F6FE`).
- **Biometric Authenticate Trigger:** Gradient pill background from `#2563EB` to `#1D4ED8` featuring a micro-pulsing voice wave icon.

### Segmented Controls & Pills
- **Toggle Base:** Enclosed frosted pill bar (`rgba(224, 236, 252, 0.6)`) with `4px` internal padding.
- **Active Segment:** Elevated white pill with micro-shadow (`0 2px 8px rgba(0,0,0,0.06)`) and bold navy text; inactive segments render in muted slate (`#64748B`).

### Status Badges & Verification Chips
- **Voice Match Confirmed:** Tinted mint background (`#ECFDF5`), emerald border (`#A7F3D0`), text `#065F46`, paired with an 8px glowing green indicator dot.
- **Spoof / Fraud Alert:** Coral blush background (`#FEF2F2`), border (`#FECACA`), text `#991B1B`.
- **In-Progress Audio Ingestion:** Subtle ice-blue background (`#EFF6FF`), cobalt text (`#1D4ED8`), dynamic waveform micro-animation.

### Cards & Analytical Panels
- **Standard Card:** Crisp `#FFFFFF` surface, `16px` border-radius, `1px solid rgba(219, 234, 254, 0.6)` outline, `space-lg` padding. Features an optional circular top-right action arrow indicator (`#2563EB` in a `#EFF6FF` disc).
- **Luminous Metric Card:** Light gradient surface transition from `#F0F6FE` to `#FFFFFF` accented with a deep cobalt headline number (`36px` bold).

### Input Fields & Controls
- **Text & Policy Search Fields:** Soft ice background (`#F8FAFC`), border `1px solid #E2E8F0`, rounded `12px` geometry. On focus: transitions to white background, cobalt border (`#2563EB`), and a soft outer glow ring (`box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12)`).
- **Checkboxes & Radios:** Pill-aligned geometry with cobalt active fill and crisp white glyph checkmarks.

### Voice Telemetry & Biometric Oscilloscope
- **Acoustic Waveform Display:** Container housed in translucent frosted white with embedded animated canvas bars varying in heights (from `#93C5FD` to `#2563EB`). Accompanied by a real-time confidence score gauge (0–100%) surrounded by a micro-radial SVG progress stroke.