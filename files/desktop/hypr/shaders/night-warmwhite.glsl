#version 300 es
// Managed by t2-mac-kde (desktop). Warm only bright, nearly neutral highlights.
precision highp float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

void main() {
    vec4 px = texture(tex, v_texcoord);
    float brightest = max(px.r, max(px.g, px.b));
    float darkest = min(px.r, min(px.g, px.b));
    // Compress highlights above 0.60; pure white reaches 0.78 instead of 1.0.
    // Include tinted off-white backgrounds, but leave saturated colours alone.
    float neutral = 1.0 - smoothstep(0.08, 0.32, brightest - darkest);
    vec3 compressed = min(px.rgb, vec3(0.60)) + max(px.rgb - 0.60, vec3(0.0)) * 0.45;
    float highlight = smoothstep(0.60, 1.0, brightest);
    vec3 paper = compressed * mix(vec3(1.0), vec3(1.0, 0.96, 0.88), highlight);
    fragColor = vec4(mix(px.rgb, paper, neutral), px.a);
}
