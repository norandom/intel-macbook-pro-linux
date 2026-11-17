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

void main() {
    vec4 px = texture(tex, v_texcoord);
    float value = gray(px.rgb);
    // Preserve dark/mid tones, compress highlights to a soft gray-white ceiling.
    value = min(value, 0.60) + max(value - 0.60, 0.0) * 0.45;
    fragColor = vec4(vec3(value), px.a);
}
