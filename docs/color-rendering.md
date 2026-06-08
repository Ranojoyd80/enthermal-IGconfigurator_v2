# Glass Color Rendering — CIE L\*a\*b\* to Screen Pixels

> How the Enthermal™ Configurator converts measured reflected-color data into the tinted glass preview shown in the **Glass Color** viz card.

This document traces one full render cycle: from the raw L\*a\*b\* numbers stored in `DATA` / `DATA_PLUS`, through the color-space conversion, to the final CSS gradient painted onto the mock window frame.

---

## 1. Where the color data lives

Every configuration row in the embedded datasets carries **two** reflected-color triplets — one for each side of the glass assembly:

| Field | Meaning |
|---|---|
| `extL`, `extA`, `extB` | Exterior reflected color (what you see from outside the building) |
| `intL`, `intA`, `intB` | Interior reflected color (what you see from inside) |

These are CIE 1976 L\*a\*b\* values computed by LBNL Windows 7 / PyWinCalc under the D65 illuminant and 2° observer, then embedded directly into the HTML as JavaScript object literals. No fetch, no runtime I/O.

> **Why Lab and not RGB?** Lab is device-independent and perceptually uniform — it is the canonical output of spectral glazing calculations. The configurator converts to sRGB only at the very last step, for display.

---

## 2. Which side is shown — the flip flag

A single module-level boolean controls which triplet feeds the renderer:

```js
let showInterior = false;           // enthermal-configurator.html:553
```

The circular **FLIP** button under the color card toggles this flag:

```js
flipBtn.addEventListener('click', function(){
  showInterior = !showInterior;
  flipBtn.classList.toggle('active', showInterior);
  // re-run updateColor() with the current match …
});
```
*(enthermal-configurator.html:723)*

When `showInterior` is `true`, the card title switches to **"Interior Reflected Color"** and the button gains its dark `.active` style.

---

## 3. The conversion pipeline — `labToRgb(L, a, b)`

Defined on one dense line at **enthermal-configurator.html:551**, this is the entire color-space conversion. Expanded for readability:

```js
function labToRgb(L, a, b) {
  // --- Step A: Lab → XYZ (D65 whitepoint, 2° observer) ---
  let fy = (L + 16) / 116;
  let fx = a / 500 + fy;
  let fz = fy - b / 200;

  const d  = 6 / 29;            // CIE linearity threshold
  const xn = 0.95047,           // D65 reference white
        yn = 1.00000,
        zn = 1.08883;

  // Inverse of the f(t) companding function used in Lab
  let x = xn * (fx > d ? fx*fx*fx : (fx - 16/116) * 3 * d*d);
  let y = yn * (fy > d ? fy*fy*fy : (fy - 16/116) * 3 * d*d);
  let z = zn * (fz > d ? fz*fz*fz : (fz - 16/116) * 3 * d*d);

  // --- Step B: XYZ → linear sRGB (Bradford-adapted D65 matrix) ---
  let rl =  3.2404542*x - 1.5371385*y - 0.4985314*z;
  let gl = -0.9692660*x + 1.8760108*y + 0.0415560*z;
  let bl =  0.0556434*x - 0.2040259*y + 1.0572252*z;

  // --- Step C: linear sRGB → gamma-corrected sRGB (companding) ---
  const g = c => c <= 0.0031308
    ? 12.92 * c
    : 1.055 * Math.pow(c, 1/2.4) - 0.055;

  // --- Step D: scale to 8-bit and clamp to valid display range ---
  return {
    r: Math.round(Math.min(255, Math.max(0, g(rl) * 255))),
    g: Math.round(Math.min(255, Math.max(0, g(gl) * 255))),
    b: Math.round(Math.min(255, Math.max(0, g(bl) * 255)))
  };
}
```

### What each step does

1. **Lab → XYZ.** Undoes the perceptual cube-root companding that Lab applies to XYZ. The piecewise branch on `d = 6/29` handles the linear segment near black where the cube-root approximation breaks down.
2. **XYZ → linear sRGB.** A standard 3×3 matrix multiplication against the Bradford-adapted D65-to-sRGB primaries.
3. **Linear → gamma-corrected sRGB.** Applies the sRGB transfer function so the values are ready for a display that expects gamma-encoded input. The piecewise branch at `0.0031308` again handles the dark toe.
4. **Clamp + quantize.** Out-of-gamut Lab coordinates (common for highly saturated glass tints) can produce negative or >1.0 linear values; these get clamped into `[0, 255]` 8-bit integers.

The result is a plain `{r, g, b}` object of integers ready for a CSS `rgb(...)` string.

---

## 4. Painting the glass — `updateColor(match)`

With RGB in hand, the app paints a single DOM element: `#fvGlass`. The rendering logic lives at **enthermal-configurator.html:707–719**:

```js
function updateColor(match) {
  if (!match) match = findMatch();
  if (!match) return;

  // Pick the triplet that matches the current flip state
  var L = showInterior ? match.intL : match.extL,
      a = showInterior ? match.intA : match.extA,
      b = showInterior ? match.intB : match.extB;

  var rgb = labToRgb(L, a, b);
  var side = showInterior ? 'Interior Reflected' : 'Exterior Reflected';

  // Build a 3-stop gradient: lighter top-left → base → darker bottom-right
  var r = rgb.r, g = rgb.g, bv = rgb.b;
  var lightR = Math.min(255, r + 25),
      lightG = Math.min(255, g + 25),
      lightB = Math.min(255, bv + 25);
  var darkR  = Math.max(0,   r - 10),
      darkG  = Math.max(0,   g - 10),
      darkB  = Math.max(0,   bv - 10);

  var glassGrad =
    'linear-gradient(170deg, ' +
      'rgb(' + lightR + ',' + lightG + ',' + lightB + ') 0%, ' +
      'rgb(' + r      + ',' + g      + ',' + bv     + ') 50%, ' +
      'rgb(' + darkR  + ',' + darkG  + ',' + darkB  + ') 100%)';

  document.getElementById('fvGlass').style.background  = glassGrad;
  document.getElementById('colorViewTitle').textContent = side + ' Color';
  document.getElementById('colorInfo').innerHTML =
    'L* ' + L.toFixed(1) +
    ' &nbsp; a* ' + a.toFixed(1) +
    ' &nbsp; b* ' + b.toFixed(1);
}
```

### Why three stops, not one flat color?

A solid fill reads as "paint chip", not "glass". The ±25 / ±10 channel shifts give the pane a subtle diagonal falloff — brighter near the sun-facing corner, a touch darker at the opposite corner — which the eye parses as a reflective surface rather than a swatch.

The shifts are asymmetric (**+25 up, −10 down**) on purpose: highlights should read more strongly than shadows on architectural glass, since most of the visual interest comes from reflected sky.

---

## 5. The static sheen overlay

On top of the dynamic tinted gradient sits a fixed CSS pseudo-element that never changes across configurations. Defined at **enthermal-configurator.html:101**:

```css
.window-flat-glass::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(170deg,
    rgba(255,255,255,.18) 0%,
    rgba(255,255,255,.05) 35%,
    transparent           55%,
    rgba(0,0,0,.02)      100%);
  pointer-events: none;
}
```

This sells the "pane of glass" illusion: a faint white highlight band across the top third plus a whisper of shadow at the bottom, identical for every configuration. Because it's a separate layer, it composites **over** the Lab-derived tint without affecting the math — swap the configuration and only the base color changes.

---

## 6. The frame

The full preview is three nested elements:

```html
<div class="window-flat">                  <!-- dark border + drop shadow -->
  <div class="window-flat-glass" id="fvGlass"></div>
                                           <!-- ::after sheen added by CSS -->
</div>
```

Styled at **enthermal-configurator.html:99–101**:

| Element | Role |
|---|---|
| `.window-flat` | 220 × 329 px window mock. `border: 10px solid #1a1d24` is the mullion, `box-shadow: 6px 10px 30px rgba(0,0,0,.18)` is the drop shadow. |
| `.window-flat-glass` (`#fvGlass`) | Gradient carrier. `transition: background .5s` cross-fades between configurations. |
| `.window-flat-glass::after` | Static sheen (see above). |

The `.5s` background transition on `#fvGlass` is what makes color changes feel smooth when the user toggles flip or switches configurations — the browser animates between the two multi-stop gradients automatically.

---

## 7. End-to-end render sequence

Putting it together, one user interaction — say, flipping the side button — triggers:

1. `flipBtn` click handler toggles `showInterior` → sets `.active` class.
2. Handler calls `updateColor(match)` (or `findPlusMatch()` for the Plus tab).
3. `updateColor` selects the correct L\*/a\*/b\* fields.
4. `labToRgb` runs Lab → XYZ → linear sRGB → gamma sRGB → 8-bit RGB.
5. Helper math derives the `+25` highlight and `−10` shadow stops.
6. The composed `linear-gradient(...)` string is assigned to `#fvGlass.style.background`.
7. Browser cross-fades the new gradient over 500 ms via CSS transition.
8. Title and L\*a\*b\* readout under the swatch update in the same call.

No canvas, no SVG, no image assets — the entire glass visualization is CSS-plus-JS math against hardcoded Lab values from LBNL calculations.

---

## 8. Reference — code locations

| Purpose | File : Line |
|---|---|
| Flip state flag | enthermal-configurator.html:553 |
| `labToRgb()` one-liner | enthermal-configurator.html:551 |
| `updateColor()` painter | enthermal-configurator.html:707–719 |
| `flipBtn` click handler | enthermal-configurator.html:723 |
| `.window-flat-glass` / `::after` styles | enthermal-configurator.html:99–101 |
| `#fvGlass` DOM element | enthermal-configurator.html:455 |
| Flip button + label | enthermal-configurator.html:460–461 |
