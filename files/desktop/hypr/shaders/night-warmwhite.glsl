#version 300 es
// Managed by t2-mac-kde (desktop). Warm whites (hypr-nightmode, the rabbit in the bar).
// Dims and warms the white content of a pixel; saturated colours stay as they are.
// Whiteness is the darkest channel, so anti-aliased white glyph edges on a coloured
// background count as partly white (a chroma test would wrongly treat them as colour).
// The white target depends on the surroundings: large white areas (pages) get a gentle
// cap, white text and lines on darker backgrounds a stronger one.
precision highp float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

const float KNEE = 0.60;        // channels below this are unchanged
const float PAGE_WHITE = 0.86;  // white inside white surroundings (browser page)
const float TEXT_WHITE = 0.68;  // white on dark/coloured surroundings (terminal text)
const float RADIUS = 10.0;      // surround sample distance, physical pixels
const vec3 CREAM = vec3(1.0, 0.96, 0.88);

float darkest(vec3 c) { return min(c.r, min(c.g, c.b)); }

void main() {
    vec4 px = texture(tex, v_texcoord);
    float white = smoothstep(0.35, 0.80, darkest(px.rgb));
    if (white <= 0.0) { fragColor = px; return; }

    vec2 d = RADIUS / vec2(textureSize(tex, 0));
    float surround = 0.0;
    for (int i = 0; i < 8; i++) {
        float a = float(i) * 0.7853982;
        surround += darkest(texture(tex, v_texcoord + d * vec2(cos(a), sin(a))).rgb);
    }
    surround /= 8.0;

    float top = mix(TEXT_WHITE, PAGE_WHITE, smoothstep(0.35, 0.85, surround));
    vec3 compressed = min(px.rgb, vec3(KNEE)) + max(px.rgb - KNEE, vec3(0.0)) * ((top - KNEE) / (1.0 - KNEE));
    float highlight = smoothstep(KNEE, 1.0, max(px.r, max(px.g, px.b)));
    vec3 paper = compressed * mix(vec3(1.0), CREAM, highlight);
    fragColor = vec4(mix(px.rgb, paper, white), px.a);
}
