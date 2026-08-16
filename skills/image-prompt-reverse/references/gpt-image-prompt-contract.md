# GPT Image prompt contract

## Goal

Write one self-contained English generation brief that reconstructs the supplied image from text alone. The image-generation tool will not receive the reference image.

## Format

Use short labeled lines. Include only labels that carry useful information, in this order:

```text
Use case: <photorealistic-natural | product-mockup | ui-mockup | infographic-diagram | scientific-educational | ads-marketing | productivity-visual | logo-brand | illustration-story | stylized-concept | historical-scene>
Asset type: reference-image reconstruction
Primary request: <literal subject, action, and intended visual result>
Scene/backdrop: <setting and depth layers>
Subject: <appearance, pose, relationships, and decisive props>
Style/medium: <photo, illustration, 3D, collage, print, or hybrid method>
Composition/framing: <exact reduced aspect ratio, orientation, shot size, viewpoint, placement, negative space>
Lighting/mood: <direction, softness, contrast, color temperature, atmosphere>
Color palette: <three to five measured hex colors with their visual roles>
Color distribution: <large-scale placement of light, dark, warm, cool, neutral, and accent fields from the blurred map>
Color-map reference: Use the attached blurred map only for coarse color and luminance placement; render the described scene with full natural detail and do not reproduce the map's blur.
Materials/textures: <specific surface and image texture>
Text (verbatim): "<exact visible text>"
Constraints: <must-preserve requirements stated positively>
Avoid: <only the few likely failure modes>
```

## Content rules

- Put subject and action in `Primary request`; do not bury them in later lines.
- Use the exact aspect ratio reported by the analyzer, not a guessed common ratio.
- Use measured colors as anchors while describing their roles, not as a disconnected hex list.
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

The prompt must stand alone. A generator that cannot see the original should still know what to depict, how to frame it, how to light it, which colors dominate, what surfaces look like, what text to render, and which accidental additions to avoid.
