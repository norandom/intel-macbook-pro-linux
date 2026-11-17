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
    // Only the top end of the tone range; saturated colours remain unchanged.
    float highlight = smoothstep(0.82, 0.98, darkest);
    float neutral = 1.0 - smoothstep(0.03, 0.12, brightest - darkest);
    vec3 cream = px.rgb * vec3(1.0, 0.95, 0.84);
    fragColor = vec4(mix(px.rgb, cream, highlight * neutral), px.a);
}
