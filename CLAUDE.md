# Enthermal™ Product Configurator — Project Rules

> **CLAUDE.md** — Standing instructions for Claude Code. Read automatically on every session.
> These rules ensure all generated code is consistent with the existing V24 codebase.

---

## 1. Architecture — Non-Negotiable Constraints

- **Single self-contained HTML file.** The entire application lives in one `.html` file (~99 KB). All CSS is in a `<style>` block, all JS in a `<script>` block. There are no external CSS or JS files.
- **Zero dependencies.** No React, no Tailwind, no npm, no build step. The only external resource is Google Fonts CDN.
- **Vanilla stack only.** HTML5, CSS3, JavaScript ES6. No frameworks, no libraries, no transpilation.
- **No separate files.** Never create standalone `.css`, `.js`, or `.json` files unless explicitly asked to separate data.

When the Figma MCP returns React + Tailwind code (its default), **translate it** into the patterns described below. Do not paste React/Tailwind output directly.

---

## 2. CSS Design Tokens

All styling MUST use these CSS custom properties. Never use raw hex values or Tailwind utility classes.

### Colors
```
--lw-dark: #0a0f1a        /* Primary text, header bg, active tab */
--lw-dark-2: #111827       /* Dark bg variant */
--lw-dark-3: #1a2236       /* Hero gradient end */
--lw-white: #fff           /* Card backgrounds */
--lw-gray-50: #f8fafc      /* Page background, light card bg */
--lw-gray-100: #f1f5f9     /* Tab background, row dividers */
--lw-gray-200: #e2e8f0     /* Card borders, dividers, toggle bg */
--lw-gray-300: #cbd5e1     /* Hover borders */
--lw-gray-400: #94a3b8     /* Callout lines, unit text, section labels */
--lw-gray-500: #64748b     /* Labels, secondary text */
--lw-gray-600: #475569     /* Summary text */
--lw-gray-700: #334155     /* Dark gray */
--lw-teal: #0d9488         /* Accent — selected states, toggles, indicators */
--lw-teal-light: #14b8a6   /* Header badge */
--lw-navy: #0f2a4a         /* Metric value gradient end */
```

### Typography
```
--font-display: 'Plus Jakarta Sans', sans-serif   /* Headings, values, labels, badges */
--font-body: 'DM Sans', sans-serif                /* Body text, form fields, descriptions */
```

### Type Scale — ONLY These 6 Sizes
```
9px   — Radio units, callout text, flip label, toggle labels
11px  — Section labels, tab text, viz card headers, badge
13px  — Field labels, select fields, summary text, config section labels
15px  — Radio values
25px  — Metric card values
32px  — Hero h1 title
```
Do NOT introduce any font sizes outside this scale.

---

## 3. Component Patterns

### Config Section
```html
<div class="config-section">
  <div class="config-section-label">SECTION NAME</div>
  <div class="config-field">
    <label>Field Label</label>
    <!-- select or radio-group goes here -->
  </div>
</div>
```
- Sections have `margin-bottom: 18px`, `padding-bottom: 18px`, `border-bottom: 1px solid var(--lw-gray-200)`
- Last section in a group: no border-bottom, no margin-bottom

### Select Dropdown
```html
<select id="uniqueId">
  <option value="" disabled selected>Select…</option>
</select>
```
- Styled via `.config-field select` — 9px 12px padding, 1.5px border, 9px border-radius
- Custom chevron via data URI SVG background-image
- Focus: border-color var(--lw-dark), box-shadow 0 0 0 3px rgba(10,15,26,.08)

### Radio Group (Thickness Selector)
```html
<div class="radio-group">
  <div class="radio-option">
    <input type="radio" name="groupName" id="id1" value="4mm">
    <label class="radio-label" for="id1">
      <span class="radio-value">4</span>
      <span class="radio-unit">mm</span>
    </label>
  </div>
  <!-- repeat for each option -->
</div>
```
- Selected state: border-color var(--lw-teal), background #f0fdfa, box-shadow 0 0 0 3px rgba(13,148,136,.1)
- Disabled state: opacity .3, cursor not-allowed, background var(--lw-gray-100)

### Toggle Switch (Two-Option Slider)
```html
<div class="srf-toggle-row">
  <span class="srf-toggle-row-label active" id="labelLeft">Left Option</span>
  <label class="srf-toggle" id="toggleId">
    <input type="checkbox" id="toggleInput">
    <span class="srf-toggle-thumb" id="thumbId"></span>
  </label>
  <span class="srf-toggle-row-label" id="labelRight">Right Option</span>
</div>
```
- Thumb: 20px circle, background var(--lw-teal), positioned via JS `thumb.style.left`
- Disabled: `.srf-toggle.disabled` — opacity .35, cursor not-allowed, thumb bg var(--lw-gray-400)
- Active label gets `.active` class: color var(--lw-dark)

### Metric Card
```html
<div class="metric-card">
  <div class="metric-label">Label Text</div>
  <div class="metric-value" id="metricId">—</div>
  <div class="metric-unit">unit text</div>
</div>
```
- Value font: 25px/800 Plus Jakarta Sans, gradient fill (linear-gradient 135deg #3b82c4 → var(--lw-navy))
- FadeIn animation on update: `animation: fadeIn .4s ease-out` (translateY 6px → 0, opacity 0 → 1)
- Dual-value cards split with a 1px vertical divider

### Viz Card (Cross-Section / Color Display)
```html
<div class="viz-card viz-cross">
  <div class="viz-card-header">
    <svg><!-- icon --></svg> HEADER TEXT
  </div>
  <div class="viz-card-body">
    <!-- content -->
  </div>
</div>
```
- 14px border-radius, 1px border var(--lw-gray-200), overflow hidden
- Header: 11px/700 uppercase, 1.5px letter-spacing, color var(--lw-gray-500)

### Vacuum Indicator
```html
<div class="vacuum-indicator">
  <div class="vacuum-dot"></div>
  <div class="vacuum-text">0.25 mm <span>— Sealed vacuum</span></div>
</div>
```
- Green pulsing dot: 7px circle, animation `pulse 2s ease-in-out infinite`

---

## 4. Layout Rules

### Main Grid
```css
.main {
  max-width: 1320px;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 14px;
}
```
- Left column: 320px config panel (fixed width)
- Right column: results grid (flexible)
- Responsive breakpoint at 1024px: collapses to single column

### Results Grid
```css
.results-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
```
- Row 1: Summary bar + Download button (full span, 1fr + 120px)
- Row 2: Two metric card groups (each internally 1fr 1fr or 1fr 120px)
- Row 3: Cross-section card + Color card (full span, side by side)

### Shared Spacing Values
- Card padding: 18px 14px 14px (metric cards), 24px (viz card body)
- Card border-radius: 12px (metric), 14px (viz/summary), 16px (config panel)
- Gap between cards: 14px
- Config body padding: 30px 22px 24px
- Section margin/padding: 18px bottom

---

## 5. JavaScript Patterns

### Data Storage
- All data is embedded as `const DATA = [...]` and `const DATA_PLUS = [...]` arrays
- No fetch calls, no external JSON files (unless migrating)
- Derived fields computed at runtime: `outerThickness`, `outerColorName`, `innerThickness`

### Cascading Filter Logic
Both tabs implement constraint propagation — each selection filters downstream options:

**Enthermal:** Outer Thickness → Low-E Coating → Substrate Color → Inner Thickness (auto-constrained) → Results

**Plus:** Outer Coating → VIG Coating (filtered) → Coating Surface S4/S5 (auto-constrained) → Results

- Invalid options: `disabled=true`, label opacity 0.3, cursor not-allowed
- When current selection becomes invalid: auto-select first valid option
- Helper functions: `unique()`, `getVal()`, `populateSelect()`

### DOM Updates
- Use `document.getElementById()` and `document.querySelector()` — no jQuery, no virtual DOM
- Metric updates: set `.textContent` or `.innerHTML` directly
- Animation trigger: remove `fade-in` class → force reflow with `void el.offsetWidth` → re-add class
- Cross-section centering: reset transform → `requestAnimationFrame` → measure with `getBoundingClientRect` → apply `translateX`

### Toggle Pattern (IIFE Closure)
```javascript
(function(){
  var toggle = document.getElementById('toggleId');
  var input = document.getElementById('toggleInput');
  var thumb = document.getElementById('thumbId');
  function positionThumb() {
    var w = toggle.offsetWidth;
    if (w < 1) return;
    if (input.checked) { thumb.style.left = (w - 20 - 2) + 'px'; }
    else { thumb.style.left = '2px'; }
  }
  function sync() {
    // Update labels, hidden radios, call update function
    positionThumb();
  }
  input.addEventListener('change', sync);
  window.addEventListener('resize', positionThumb);
  requestAnimationFrame(positionThumb);
})();
```

### Color Rendering
- CIE L*a*b* → XYZ (D65 illuminant) → Linear sRGB → Gamma correction → 8-bit RGB
- Glass display uses a 3-stop gradient (lighter → base → darker) for depth
- Flip button toggles between exterior reflected and interior transmitted color

---

## 6. Cross-Section Diagrams

- Built entirely with CSS — no images, no SVG, no canvas
- Glass panes: CSS gradients + box-shadows + borders
- Low-E coating lines: 1.5px absolute-positioned elements with `background: #ea580c`
- Desiccant beads (Plus): 96 CSS `radial-gradient()` layers
- Spacer bar: solid #1a1d24 rectangle at base of gap
- Callout system: dot (6px circle) + line (1px height) + text (9px uppercase)
- S4/S5 coating lines use `opacity` transitions (0.25s ease), not display toggle

---

## 7. Naming Conventions

- IDs: camelCase (`outerCoating`, `csThicknessVal`, `csPlusCalloutS2`)
- CSS classes: kebab-case (`config-field`, `metric-value`, `cs-pane-outer`)
- Data fields: camelCase matching the JSON schema (`uval`, `shgc`, `vigSurface`)
- Section labels: UPPERCASE via CSS `text-transform: uppercase`
- Product names: Use ™ symbol (Enthermal™, Enthermal Plus™)

---

## 8. Print & Responsive

- Print: hides header, hero, tabs, download button via `@media print`
- Responsive breakpoint at `max-width: 1024px`: single-column stack
- No mobile-specific UI — this is primarily a desktop tool for architects and specifiers

---

## 9. What NOT to Do

- ❌ Do NOT use React, Vue, Svelte, or any framework
- ❌ Do NOT use Tailwind utility classes (translate to CSS custom properties)
- ❌ Do NOT import npm packages
- ❌ Do NOT create a build pipeline (webpack, vite, etc.)
- ❌ Do NOT split into multiple files unless explicitly requested
- ❌ Do NOT use `localStorage`, `sessionStorage`, or cookies
- ❌ Do NOT add font sizes outside the 6-size scale (9/11/13/15/25/32)
- ❌ Do NOT use `async/await` for data — it's all synchronous embedded data
- ❌ Do NOT use `display: none/block` to toggle coating lines — use `opacity` transitions
- ❌ Do NOT use `getBoundingClientRect` without forcing reflow first (`void el.offsetWidth`)

---

## 10. Figma MCP Translation Rules

When `/implement-design` returns Figma-derived code:

1. **Replace Tailwind classes** with the CSS custom properties listed above
2. **Replace React components** with semantic HTML using the component patterns above
3. **Map Figma variables** to the `:root` tokens — if Figma uses a color not in the token set, find the closest match
4. **Match the type scale** — Figma may use arbitrary sizes; snap to the nearest value in the 6-size scale
5. **Preserve existing structure** — new UI elements should follow the grid layout and card patterns already in V24
6. **Use the existing animation patterns** — fadeIn for metric cards, opacity transitions for coating lines, pulse for indicators

---

## 11. Product Context

This is the **LuxWall Enthermal™ Product Configurator** — a technical sales tool for architects, specifiers, and the LuxWall sales team. It displays thermal performance metrics (U-value, SHGC, Tvis, R-value, OITC) for vacuum insulated glass (VIG) configurations.

**Current tabs:** Enthermal™ (60 configs), Enthermal Plus™ (36+ configs), Enthermal Spandrel (disabled/placeholder)

**Data source:** LBNL Windows 7 / PyWinCalc calculations exported to CSV, embedded as JS object arrays.

**Accuracy is critical.** All displayed performance values are validated against official LuxWall product data sheets (98%+ match rate). Never modify, round, or truncate data values.

---

## 12. Figma MCP — Required Fetch Sequence

1. Run `get_design_context` first — returns code, screenshot, and metadata in one call.
2. If the response is truncated, run `get_metadata` to get the full node map, then re-fetch specific child nodes with `get_design_context`.
3. Never skip to implementation before reading both the code output and the screenshot.
4. Always implement pixel-level diffs — do not judge any difference as "not worth changing".
