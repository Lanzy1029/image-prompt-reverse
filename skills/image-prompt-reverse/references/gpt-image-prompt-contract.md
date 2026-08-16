# GPT Image prompt contract

## Goal

Write one self-contained English generation brief that reconstructs the supplied image from text plus two deterministic derived references: the five-color palette and the blurred spatial color-distribution map. The image-generation tool will not receive the original reference image.

## Format

Use short labeled lines. Include only labels that carry useful information, in this order:

```text
Use case: <photorealistic-natural | product-mockup | ui-mockup | infographic-diagram | scientific-educational | ads-marketing | productivity-visual | logo-brand | illustration-story | stylized-concept | historical-scene>
Asset type: reference-image reconstruction
Primary request: <literal subject, action, and intended visual result>
Scene/backdrop: <setting and depth layers>
Subject: <appearance, pose, relationships, and decisive props>
Portrait appearance: <broad appearance cue when warranted plus at least five visible facial anchors, or not applicable with a reason>
Style/medium: <photo, illustration, 3D, collage, print, or hybrid method>
Composition/framing: <exact reduced aspect ratio, orientation, shot size, viewpoint, placement, negative space>
Lighting/mood: <direction, softness, contrast, color temperature, atmosphere>
Color palette: <three to five measured hex colors with their visual roles>
Palette reference: Use the attached five-color palette only for dominant hue anchors and their approximate relative importance; do not reproduce swatches, borders, labels, percentages, hex text, or the palette's graphic layout.
Color distribution: <large-scale placement of light, dark, warm, cool, neutral, and accent fields from the blurred map>
Color-map reference: Use the attached blurred map only for coarse color and luminance placement; render the described scene with full natural detail and do not reproduce the map's blur.
Materials/textures: <specific surface and image texture>
Text (verbatim): "<exact visible text>"
Constraints: <must-preserve requirements stated positively>
Avoid: <only the few likely failure modes>
```

## Content rules

- Put subject and action in `Primary request`; do not bury them in later lines.
- When `Primary request` or `Subject` contains a person, include `Portrait appearance`. If no face is visible at useful detail, write `Portrait appearance: Not applicable; <brief reason>`.
- For a visible face, describe at least five independent anchors across face shape, eyes and eyelids, brows, nose, cheeks or jaw or chin, mouth or lips, complexion and undertone, and hair. Do not use vague phrases such as `natural soft facial features` as a substitute.
- If multiple facial cues support a broad regional appearance that materially affects reconstruction, state it early with careful language such as `East Asian-presenting adult`. Treat it as a visual reconstruction cue, not verified race, ethnicity, nationality, or identity.
- Never infer a broad regional appearance from hair, skin tone, clothing, location, cultural styling, or one facial feature alone. Never use the category without the individual facial anchors.
- When demographic drift is a likely failure mode, restate the concrete facial anchors in `Constraints` and use `Avoid` for a generic or region-mismatched face template rather than for caricatured traits.
- Use the exact aspect ratio reported by the analyzer, not a guessed common ratio.
- Use measured colors as anchors while describing their roles, not as a disconnected hex list.
- State that the attached palette controls only dominant hue anchors and approximate relative importance. Explicitly forbid rendering its swatches, borders, labels, percentages, hex text, or graphic layout.
- Translate the blurred color-distribution map into explicit spatial instructions such as `warm highlight in the upper left`, `dark field across the lower third`, or `cool neutral background on the right`.
- State that the attached blurred map controls only coarse color and luminance placement. Do not ask the generator to reproduce its blur, invent subjects from it, or treat it as the original image.
- Describe real texture concretely: skin pores, worn fabric, matte ceramic, halftone dots, paper fibers, brush edges, film grain, or settled dust only when visible.
- Treat inferred focal length and aperture as visual equivalents, not camera metadata facts.
- Put any required rendered text in quotation marks, with placement and typography guidance. Omit the `Text` line if no text is visible.
- State constraints positively where possible. Use `Avoid` only for likely additions or distortions such as extra text, extra limbs, watermarks, logos, or unobserved props.
- Do not include model parameters, API options, seed values, JSON, Markdown fences, explanations, or multiple prompt variants.
- Do not use a living artist's name or identify a real person.
- Do not use empty boosters such as `masterpiece`, `best quality`, `8k`, `ultra detailed`, or `cinematic` without a concrete visual explanation.

## Reconstruction versus transfer

For default reconstruction, retain the same visible subject, setting, composition, and text. For user-requested transfer, change only the requested content and keep the source's compositional, lighting, color, texture, and camera logic.

## Final check

The prompt must stand alone. A generator that cannot see the original should still know what to depict, how each visible person looks without relying on a demographic label alone, how to frame and light the scene, which palette colors dominate, where the large color fields sit, what surfaces look like, what text to render, and which accidental additions to avoid.
