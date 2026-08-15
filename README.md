# Image Prompt Reverse

`image-prompt-reverse` is a reusable Codex Skill that turns a reference image into an auditable GPT Image reconstruction bundle.

Given an attached image, the Skill:

1. inspects the reference and measures its dimensions, aspect ratio, tonal profile, and representative colors;
2. writes a step-by-step reverse-engineering report;
3. extracts one executable English GPT Image prompt from the report;
4. calls the built-in GPT image-generation tool using the extracted text prompt;
5. compares the generated image with the reference; and
6. returns the original image, palette, report, prompt, generated image, and verification manifest together.

## Example: Sunlit Camera Portrait

The reconstruction below was generated from the extracted text prompt only. The GPT Image generation step did not receive the reference image as an editing input.

<table>
  <tr>
    <th width="50%">Input reference</th>
    <th width="50%">Prompt-only GPT Image reconstruction</th>
  </tr>
  <tr>
    <td width="50%"><img src="./examples/sunlit-camera-portrait/original-image.png" alt="Input reference: sunlit portrait of a woman holding a compact camera" width="100%"></td>
    <td width="50%"><img src="./examples/sunlit-camera-portrait/generated-image.png" alt="GPT Image prompt-only reconstruction of the sunlit camera portrait" width="100%"></td>
  </tr>
</table>

The reconstruction preserves the direct gaze, compact-camera pose, black bob and bangs, gingham-trimmed ivory outfit, backlit street setting, and muted cream-and-teal palette. Its clearest deviation is a cleaner exposure with less of the original's broad cyan-white veiling flare.

![Measured five-color palette](./examples/sunlit-camera-portrait/color-palette.png)

Explore the complete audit trail:

- [Step-by-step reverse-engineering report](./examples/sunlit-camera-portrait/reverse-engineering.md)
- [Extracted GPT Image prompt](./examples/sunlit-camera-portrait/gpt-image-prompt.txt)
- [Objective image analysis](./examples/sunlit-camera-portrait/image-analysis.json)
- [Verified bundle manifest](./examples/sunlit-camera-portrait/bundle-manifest.json)

## Install

After this repository is published, ask Codex to install the Skill from:

```text
https://github.com/Lanzy1029/image-prompt-reverse/tree/main/skills/image-prompt-reverse
```

For manual installation, copy `skills/image-prompt-reverse` into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/image-prompt-reverse ~/.codex/skills/
```

You can also download `release/image-prompt-reverse.skill.zip`, extract it, and place the resulting `image-prompt-reverse` directory under `~/.codex/skills/`.

## Use

Attach an image and ask:

```text
Use $image-prompt-reverse to reverse-engineer this image and generate a prompt-only reconstruction.
```

The Skill creates a new directory under `promptgen-output/` containing:

```text
original-image.<ext>
color-palette.png
image-analysis.json
reverse-engineering.md
gpt-image-prompt.txt
generated-image.<ext>
bundle-manifest.json
```

## Requirements

- Codex with image viewing and the built-in GPT image-generation tool.
- Python 3.10 or newer.
- At least one supported image decoder: Pillow, FFmpeg, or ImageMagick.

No OpenAI API key is required for the default built-in generation path. The reconstruction stage sends the extracted text prompt to the image-generation tool without attaching the reference image as an editing input.

## Repository layout

```text
skills/image-prompt-reverse/  Installable Skill source
examples/                     Complete verified example bundle
release/                      Downloadable Skill archive
```

This repository includes one demonstration bundle. Only add or redistribute reference images when you have permission to publish them.

## License

MIT
