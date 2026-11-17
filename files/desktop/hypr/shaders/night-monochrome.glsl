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

// Static 4x4 ordered dithering retains shading using only black and white.
// Screen-pixel coordinates keep the pattern stable; there is no temporal flicker.
const int bayer[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
void main() {
    vec4 px = texture(tex, v_texcoord);
    ivec2 cell = ivec2(gl_FragCoord.xy) % 4;
    float threshold = (float(bayer[cell.y * 4 + cell.x]) + 0.5) / 16.0;
    fragColor = vec4(vec3(step(threshold, gray(px.rgb))), px.a);
}
