#version 300 es
// Managed by t2-mac-kde (desktop). Whole-screen rabbit filter.
precision highp float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

float gray(vec3 rgb) {
    vec3 linear = mix(rgb / 12.92, pow((rgb + 0.055) / 1.055, vec3(2.4)), step(0.04045, rgb));
    float luminance = dot(linear, vec3(0.2126, 0.7152, 0.0722));
    return luminance <= 0.0031308 ? 12.92 * luminance : 1.055 * pow(luminance, 1.0 / 2.4) - 0.055;
}

// Four shades like a reflective 1990s LCD: charcoal ink on gray-green glass.
// A small, static dither only softens shade boundaries; no full-range stippling.
const int bayer[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
const vec3 ink = vec3(0.12, 0.17, 0.13);
const vec3 glass = vec3(0.73, 0.77, 0.64);
void main() {
    vec4 px = texture(tex, v_texcoord);
    ivec2 cell = ivec2(gl_FragCoord.xy) % 4;
    float dither = (float(bayer[cell.y * 4 + cell.x]) + 0.5) / 16.0 - 0.5;
    float tone = clamp(gray(px.rgb) * 3.0 + dither * 0.22, 0.0, 3.0);
    float shade = floor(tone + 0.5) / 3.0;
    fragColor = vec4(mix(ink, glass, shade), px.a);
}
