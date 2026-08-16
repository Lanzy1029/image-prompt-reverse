# Reverse-Analysis and Report Contract

## Contents

- [Purpose](#purpose)
- [Analysis rules](#analysis-rules)
- [Required report structure](#required-report-structure)
- [Post-generation appendix](#post-generation-appendix)

## Purpose

Produce an evidence-led English reconstruction report that shows how the final prompt was derived. Keep the report useful even if image generation is unavailable.

## Analysis rules

1. Start with the image's communicative purpose and visual hierarchy, not a noun inventory.
2. Distinguish measured facts, visible observations, and inferred production choices.
3. Convert every decisive observation into an executable prompt instruction.
4. Preserve literal subject and scene details in reconstruction mode.
5. In transferable-style mode, preserve visual decisions but replace content only as the user requested.
6. Use exact visible text in quotation marks. If characters are unreadable, write `unclear`; do not complete them by guesswork.
7. Avoid empty quality boosters such as `masterpiece`, `best quality`, `8k`, `award-winning`, or `ultra detailed`.
8. Describe a real person through visible traits, pose, expression, wardrobe, and lighting rather than naming them.
9. Do not name a living artist. Describe movements, media, brushwork, geometry, texture, and palette instead.
10. Preserve the exact reduced aspect ratio from `image-analysis.json`.
11. Use `color-distribution-map.png` only to measure large-scale spatial color and luminance placement; never infer identity, text, objects, or fine composition from the blurred map.

## Required report structure

Use these headings in exactly this order. Add detail inside a section rather than adding new top-level sections before generation validation.

````markdown
# GPT Image Reverse-Engineering Report

## Deliverable Preview

### Original Image
![Original image](./original-image.<ext>)

### Color Palette
![Color palette](./color-palette.png)

### Blurred Color Distribution Map
![Blurred color distribution map](./color-distribution-map.png)

## Step 0 - Objective Measurements

- File:
- Pixel dimensions:
- Exact aspect ratio:
- Orientation:
- Dominant colors and estimated area ratios:
- Temperature / contrast / saturation:

## Step 1 - Image Purpose and Visual Thesis

Use one sentence to explain what the image makes the viewer feel first and its most likely intended use.

## Step 2 - Subject, Action, and Visible Elements

Describe appearance, pose, action, relationships, and decisive props. Separate certain details from unclear ones.

## Step 3 - Composition and Spatial Hierarchy

Describe shot size, subject placement, foreground/midground/background, eye path, negative space, balance, cropping, and aspect ratio.

## Step 4 - Lighting System

Describe key-light direction, softness, temperature, fill, rim light, contrast, shadows, reflections, and time-of-day cues.

## Step 5 - Color System

Reference the measured palette and blurred color-distribution map. Explain color roles, warm/cool relationships, saturation strategy, tonal range, focal emphasis, and where the largest color and luminance fields sit in the frame.

## Step 6 - Style, Medium, and Surface Texture

Describe photography, illustration, 3D, or mixed media; materials; grain; brushwork; edges; detail-density distribution; and post-processing traits.

## Step 7 - Camera, Viewpoint, and Motion

Give camera language that plausibly explains the image. Mark uncertain focal lengths or apertures as inferences and include confidence.

## Step 8 - Text and Graphic Elements

Record clearly visible wording verbatim and describe its typographic character, color, and placement. If there is no visible text, write `No visible text`.

## Step 9 - Mood, Narrative, and Energy

Provide a one-sentence emotional thesis, three mood words, implied story, and static or dynamic energy state.

## Step 10 - Decisive Features and Prompt Translation

List five to eight of the most important image-evidence-to-prompt-instruction translations and label evidence level and confidence.

| Image evidence | Prompt instruction | Evidence level | Confidence |
|---|---|---|---|
| ... | ... | measured / visible / inferred | high / medium / low |

## GPT Image Prompt

<!-- GPT_IMAGE_PROMPT_START -->
```text
<one executable English prompt following gpt-image-prompt-contract.md>
```
<!-- GPT_IMAGE_PROMPT_END -->

## Prompt Self-Check

- Subject and action covered: yes / no
- Composition and exact aspect ratio covered: yes / no
- Lighting, measured palette, and spatial color distribution covered: yes / no
- Materials and style covered: yes / no
- Visible text quoted verbatim or explicitly absent: yes / no
- No empty quality terms, artist names, or unsupported details: yes / no
````

## Post-generation appendix

After generation, append this material to the same file:

```markdown
## Generation Validation

### Generated Image
![Generated image](./generated-image.<ext>)

### Comparison Conclusion

Compare composition, lighting, color, materials, subject fidelity, and large-scale spatial color placement in one concise paragraph.

### Three Strongest Matches

1. ...
2. ...
3. ...

### Three Clearest Deviations

1. ...
2. ...
3. ...

### Next-Pass Recommendation

Recommend only the single most valuable prompt change. Do not silently rewrite the extracted prompt or regenerate during the current pass.
```
