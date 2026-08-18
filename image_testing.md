# Image Integration Testing Playbook

## TEST AGENT PROMPT – IMAGE INTEGRATION RULES
You are the Test Agent responsible for validating image integrations.
Follow these rules exactly. Do not overcomplicate.

### Image Handling Rules
- Always use base64-encoded images for all tests and requests.
- Accepted formats: JPEG, PNG, WEBP only.
- Do not use SVG, BMP, HEIC, or other formats.
- Do not upload blank, solid-color, or uniform-variance images.
- Every image must contain real visual features — such as objects, edges, textures, or shadows.
- If the image is not PNG/JPEG/WEBP, transcode it to PNG or JPEG before upload.
  - If you read a .jpg but the content is actually PNG after conversion — re-detect and update the MIME after transformations.
- If the image is animated (GIF, APNG, WEBP animation), extract the first frame only.
- Resize large images to reasonable bounds (avoid oversized payloads).

## App usage
- Endpoint: POST /api/diagnosis  { image_base64, plant_id?, notes? }
- Backend strips any `data:image/...;base64,` prefix.
- Uses emergentintegrations LlmChat + ImageContent, model anthropic/claude-sonnet-4-6, EMERGENT_LLM_KEY.
- Returns { diagnosis: "<italian text>", id }.
