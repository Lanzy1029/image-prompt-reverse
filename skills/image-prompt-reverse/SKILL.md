---
name: image-prompt-reverse
description: Analyze one or more user-provided reference images, reverse-engineer their visual construction into a step-by-step English report and an executable English GPT Image prompt, create a deterministic color palette and detail-suppressed spatial color-distribution map, automatically extract the prompt, use the blurred map rather than the original image to condition GPT Image generation, compare the result, and deliver a verified reconstruction bundle. Use when the user asks to reverse-engineer an image prompt, recreate an image with GPT Image, infer a prompt from a picture, extract a palette or spatial color layout from a reference, or compare an original image with a reconstructed result.
---

# Image Prompt Reverse

Turn a supplied image into an auditable reconstruction bundle. Complete the whole workflow without stopping after analysis or asking the user to copy a prompt manually.

Version 1.2 adds a deterministic blurred color-distribution map. Use it as the only image reference during generation so GPT Image can follow the reference's large-scale color and luminance placement without receiving the original pixels or identifiable detail.

## Required references

Read both files before analyzing an image:

- `references/reverse-analysis-contract.md` for observation rules and the report contract.
- `references/gpt-image-prompt-contract.md` for the executable prompt format.

## Default behavior

- Treat one supplied image as one independent task.
- For multiple images, create one result directory per image unless the user explicitly asks for a combined visual language.
- Reconstruct the visible subject and scene by default so the generated result can test the prompt. Switch to transferable-style mode only when the user asks to replace the subject or setting.
- Write every textual artifact in English unless the user explicitly requests another language for the task output.
- Preserve the reference aspect ratio in the analysis and prompt.
- Preserve large-scale spatial color placement through the blurred distribution map while suppressing semantic detail.
- Use the built-in image-generation tool. Do not ask for an API key and do not use a browser UI or third-party service.

## Output contract

Create a unique directory under `./promptgen-output/` named with a timestamp and short source slug. Never overwrite a previous result. The completed directory must contain:

```text
promptgen-output/<timestamp>-<slug>/
├── original-image.<ext>
├── color-palette.png
├── color-distribution-map.png
├── image-analysis.json
├── reverse-engineering.md
├── gpt-image-prompt.txt
├── generated-image.<ext>
└── bundle-manifest.json
```

Treat `image-analysis.json` as objective local evidence, not as semantic image understanding. Treat visual interpretations in the report as model judgments and label uncertainty where relevant.

## Workflow

### 1. Resolve and inspect the reference

Require an actual image attachment or a readable local image path. Do not substitute an image search result or download a URL unless the user explicitly asks for that.

Inspect the source with the image-viewing tool before writing any analysis. If the image is not available as a local file, ask the user to attach it again because the deterministic palette and deliverable bundle require the source bytes.

### 2. Create the objective artifacts

Create a unique result directory, then run:

```bash
python3 <skill-dir>/scripts/analyze_reference.py <input-image> <result-dir>
```

The script preserves the source bytes as `original-image.<ext>`, extracts five representative colors, renders `color-palette.png`, creates `color-distribution-map.png`, and writes dimensions, exact reduced aspect ratio, palette ratios, spatial-map metadata, tonal profile, and hashes to `image-analysis.json`.

The color-distribution map must be deterministic and strongly detail-suppressed. Retain only coarse color fields, luminance zones, and their approximate locations. Treat it as evidence for color placement, not evidence for subject identity or object detail.

If the decoder is unavailable, report the script's actionable dependency message. Do not invent palette hex values and call them measured.

Inspect both `color-palette.png` and `color-distribution-map.png` after creation, then read `image-analysis.json` completely. If recognizable facial, textual, or object detail remains in the distribution map, treat the output as invalid and increase detail suppression before generation.

### 3. Reverse-engineer step by step

Follow `references/reverse-analysis-contract.md`. Separate three evidence levels:

1. **Measured**: dimensions, ratio, and palette values from `image-analysis.json`.
2. **Visible**: directly observable subject, layout, light, texture, and text.
3. **Inferred**: likely lens, production method, style family, or narrative; add confidence and alternatives.

Do not identify a real person from the image. Describe visible appearance. Do not name a living artist; translate influence into visual techniques.

### 4. Write the report and embed the prompt

Write `reverse-engineering.md` using the exact section order and prompt markers in `references/reverse-analysis-contract.md`. Add relative image links to the original, palette, and color-distribution map. Use the map to describe where major warm, cool, light, dark, neutral, and accent fields sit in the frame.

Build the English GPT Image prompt using `references/gpt-image-prompt-contract.md`. Put exactly one executable prompt between these markers:

````markdown
<!-- GPT_IMAGE_PROMPT_START -->
```text
<prompt>
```
<!-- GPT_IMAGE_PROMPT_END -->
````

Do not place commentary, alternatives, or a negative-prompt appendix inside the markers.

### 5. Extract the prompt mechanically

Run:

```bash
python3 <skill-dir>/scripts/extract_prompt.py \
  <result-dir>/reverse-engineering.md \
  <result-dir>/gpt-image-prompt.txt
```

Read `gpt-image-prompt.txt` back and use its contents verbatim for generation. This step is mandatory: do not retype or silently improve the prompt after extraction.

### 6. Generate from the prompt and blurred color map

Call the built-in `image_gen.imagegen` GPT image-generation tool with the extracted prompt and `color-distribution-map.png` as a reference-conditioned generation.

- Set `referenced_image_paths` to a one-item list containing only the absolute local path to `color-distribution-map.png`.
- Omit `num_last_images_to_include`.
- Never attach `original-image.<ext>` to the generation call.
- Tell the generator through the extracted prompt to use the attached blurred map only for large-scale color and luminance placement, not as a source of subjects, objects, texture, or blur.
- Generate one image by default.
- If the built-in tool is unavailable, stop and explain that the automatic generation stage could not run. Do not silently switch to an API/CLI path.

The generation tool saves under the Codex generated-images area. Copy its returned local output into the result directory with:

```bash
python3 <skill-dir>/scripts/import_generated.py <generated-local-path> <result-dir>
```

Never overwrite an existing generated image.

### 7. Inspect and close the report

Inspect the saved generated image. Append to `reverse-engineering.md`:

- a relative link to the generated image;
- a concise comparison covering composition, lighting, color, materials, and subject fidelity;
- whether the major spatial color fields match the blurred distribution map;
- the three strongest matches;
- the three clearest deviations;
- one suggested next-pass change, without changing the extracted prompt or regenerating unless the user asked for iteration.

Be candid. The generated image is a prompt reconstruction, not pixel-identical proof.

### 8. Verify the bundle

Run:

```bash
python3 <skill-dir>/scripts/verify_bundle.py <result-dir>
```

Fix every reported failure. The verifier confirms required artifacts, image signatures, distribution-map metadata, report links, and exact equality between the marked report prompt and `gpt-image-prompt.txt`, then writes `bundle-manifest.json`.

### 9. Present the result

In the final response:

- show the original image, color palette, blurred color-distribution map, and generated image inline using absolute paths;
- link the report, extracted prompt, manifest, and result directory;
- state that the built-in GPT image-generation tool was used;
- summarize the strongest match and largest deviation in one or two sentences.

Do not finish with only file paths or only the generated image. All eight artifacts are part of the result.

## Failure boundaries

- Missing image: request a new attachment.
- Unsupported/corrupt image: preserve no partial claim; report the decoder error.
- Palette failure: do not replace measured colors with guessed colors.
- Distribution-map failure: do not pass the original image as a substitute reference; retain the analysis artifacts and report the bundle incomplete.
- Prompt extraction failure: repair the report markers and extract again before generation.
- Generation failure: retain the completed analysis artifacts, clearly mark the bundle incomplete, and do not create a fake generated file or passing manifest.
- Ambiguous visible detail: write `unclear` and give at most one plausible alternative.
