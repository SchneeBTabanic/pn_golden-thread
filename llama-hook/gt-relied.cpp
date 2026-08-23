#include "gt-relied.h"

#include "ggml-backend.h"
#include "log.h"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <set>
#include <vector>

struct gt_relied_state {
    bool armed = false;
    bool skip = false;
    bool got_decode = false;
    bool saw_softmax = false;
    int n_steps = 0;
    int n_heads = 0;
    std::set<std::pair<int,int>> headset;
    std::vector<gt_relied_span> spans;
    std::vector<double> span_sum;
    std::vector<uint8_t> buf;
};

struct gt_press_state {
    bool armed = false;
    float bias = 0.0f; // log(strength), PASTA exclude
    int32_t n_prompt = 0;
    std::set<std::pair<int,int>> headset;
    std::vector<gt_relied_span> spans;
    std::vector<uint8_t> buf;
    bool applied = false;
};

struct gt_dial_mask_state {
    bool armed = false;
    std::vector<gt_relied_span> spans;
    std::vector<uint8_t> buf;
    bool applied = false;
};

static gt_relied_state g_relied;
static gt_press_state g_press;
static gt_dial_mask_state g_dial_mask;

static float gt_load_f(const uint8_t * data, ggml_type type, const size_t * nb,
                       int64_t i0, int64_t i1, int64_t i2) {
    const size_t off = (size_t) i0 * nb[0] + (size_t) i1 * nb[1] + (size_t) i2 * nb[2];
    if (type == GGML_TYPE_F32) {
        float v;
        memcpy(&v, data + off, sizeof(float));
        return v;
    }
    if (type == GGML_TYPE_F16) {
        ggml_fp16_t h;
        memcpy(&h, data + off, sizeof(ggml_fp16_t));
        return ggml_fp16_to_fp32(h);
    }
    if (type == GGML_TYPE_BF16) {
        ggml_bf16_t h;
        memcpy(&h, data + off, sizeof(ggml_bf16_t));
        return ggml_bf16_to_fp32(h);
    }
    return 0.0f;
}

static void gt_store_f(uint8_t * data, ggml_type type, const size_t * nb,
                       int64_t i0, int64_t i1, int64_t i2, float v) {
    const size_t off = (size_t) i0 * nb[0] + (size_t) i1 * nb[1] + (size_t) i2 * nb[2];
    if (type == GGML_TYPE_F32) {
        memcpy(data + off, &v, sizeof(float));
        return;
    }
    if (type == GGML_TYPE_F16) {
        ggml_fp16_t h = ggml_fp32_to_fp16(v);
        memcpy(data + off, &h, sizeof(ggml_fp16_t));
        return;
    }
    if (type == GGML_TYPE_BF16) {
        ggml_bf16_t h = ggml_fp32_to_bf16(v);
        memcpy(data + off, &h, sizeof(ggml_bf16_t));
        return;
    }
}

static bool gt_in_spans(int32_t k, const std::vector<gt_relied_span> & spans) {
    for (const auto & s : spans) {
        if (k >= s.start && k < s.end) {
            return true;
        }
    }
    return false;
}

static uint8_t * gt_tensor_bytes(struct ggml_tensor * t, std::vector<uint8_t> & buf, bool * host_out) {
    const bool is_host = t->buffer && ggml_backend_buffer_is_host(t->buffer);
    *host_out = is_host;
    if (is_host) {
        return (uint8_t *) t->data;
    }
    const size_t nbytes = ggml_nbytes(t);
    buf.resize(nbytes);
    ggml_backend_tensor_get(t, buf.data(), 0, nbytes);
    return buf.data();
}

static void gt_tensor_put(struct ggml_tensor * t, const std::vector<uint8_t> & buf, bool is_host) {
    if (is_host) {
        return;
    }
    ggml_backend_tensor_set(t, buf.data(), 0, buf.size());
}

void gt_relied_arm(
    const std::vector<std::pair<int,int>> & heads,
    const std::vector<gt_relied_span> & spans) {
    g_relied.armed = false;
    g_relied.skip = false;
    g_relied.got_decode = false;
    g_relied.saw_softmax = false;
    g_relied.n_steps = 0;
    g_relied.headset.clear();
    g_relied.spans = spans;
    g_relied.span_sum.assign(spans.size(), 0.0);
    g_relied.n_heads = 0;
    if (heads.empty() || spans.empty()) {
        return;
    }
    for (const auto & h : heads) {
        if (h.first < 0 || h.second < 0) {
            continue;
        }
        g_relied.headset.insert(h);
    }
    g_relied.n_heads = (int) g_relied.headset.size();
    if (g_relied.n_heads == 0) {
        return;
    }
    g_relied.armed = true;
}

void gt_relied_disarm() {
    g_relied.armed = false;
    g_relied.skip = false;
    g_relied.got_decode = false;
}

void gt_relied_pause() {
    g_relied.skip = true;
}

void gt_relied_resume() {
    g_relied.skip = false;
}

void gt_relied_finish_step() {
    if (!g_relied.armed || g_relied.skip) {
        return;
    }
    if (g_relied.got_decode) {
        g_relied.n_steps += 1;
    }
    g_relied.got_decode = false;
}

gt_relied_snapshot gt_relied_take() {
    gt_relied_snapshot out;
    out.n_steps = g_relied.n_steps;
    out.n_heads = g_relied.n_heads;
    out.saw_softmax = g_relied.saw_softmax;
    const double denom = (double) g_relied.n_heads * (double) g_relied.n_steps;
    for (size_t i = 0; i < g_relied.spans.size(); ++i) {
        double frac = 0.0;
        if (denom > 0.0) {
            frac = g_relied.span_sum[i] / denom;
        }
        out.fractions[g_relied.spans[i].id] = frac;
    }
    return out;
}

void gt_press_arm(
    const std::vector<std::pair<int,int>> & heads,
    const std::vector<gt_relied_span> & spans,
    float strength,
    int32_t n_prompt) {
    g_press.armed = false;
    g_press.applied = false;
    g_press.headset.clear();
    g_press.spans = spans;
    g_press.n_prompt = n_prompt;
    g_press.bias = 0.0f;
    if (strength <= 0.0f || spans.empty() || heads.empty()) {
        return;
    }
    for (const auto & h : heads) {
        if (h.first < 0 || h.second < 0) {
            continue;
        }
        g_press.headset.insert(h);
    }
    if (g_press.headset.empty()) {
        return;
    }
    g_press.bias = logf(strength);
    g_press.armed = true;
}

void gt_press_disarm() {
    g_press.armed = false;
}

bool gt_press_is_armed() {
    return g_press.armed;
}

bool gt_press_applied() {
    return g_press.applied;
}

void gt_dial_mask_arm(const std::vector<gt_relied_span> & spans) {
    g_dial_mask.armed = !spans.empty();
    g_dial_mask.applied = false;
    g_dial_mask.spans = spans;
}

void gt_dial_mask_disarm() {
    g_dial_mask.armed = false;
}

bool gt_dial_mask_applied() {
    return g_dial_mask.applied;
}

void gt_dial_mix_logits(float * cond, const float * uncond, int n_vocab, float alpha) {
    if (!cond || !uncond || n_vocab <= 0) {
        return;
    }
    const float ap = 1.0f + alpha;
    for (int i = 0; i < n_vocab; ++i) {
        cond[i] = ap * cond[i] - alpha * uncond[i];
    }
}

static void gt_mutate_kq(struct ggml_tensor * t, const char * name) {
    const int layer = atoi(name + 3);
    const int64_t n_kv   = t->ne[0];
    const int64_t n_q    = t->ne[1];
    const int64_t n_head = t->ne[2];
    if (n_kv <= 0 || n_q <= 0 || n_head <= 0) {
        return;
    }
    bool is_host = false;
    std::vector<uint8_t> * buf = g_press.armed ? &g_press.buf : &g_dial_mask.buf;
    uint8_t * data = gt_tensor_bytes(t, *buf, &is_host);
    if (data == nullptr) {
        return;
    }
    const int32_t n_prompt = g_press.n_prompt > 0 ? g_press.n_prompt : (int32_t) n_kv;
    for (int q = 0; q < (int) n_q; ++q) {
        for (int h = 0; h < (int) n_head; ++h) {
            if (g_dial_mask.armed) {
                for (int32_t k = 0; k < (int32_t) n_kv; ++k) {
                    if (gt_in_spans(k, g_dial_mask.spans)) {
                        gt_store_f(data, t->type, t->nb, k, q, h, -1.0e9f);
                    }
                }
                g_dial_mask.applied = true;
            }
            if (g_press.armed) {
                if (g_press.headset.count({layer, h}) == 0) {
                    continue;
                }
                const int32_t kmax = n_prompt < (int32_t) n_kv ? n_prompt : (int32_t) n_kv;
                for (int32_t k = 0; k < kmax; ++k) {
                    if (gt_in_spans(k, g_press.spans)) {
                        continue;
                    }
                    const float v = gt_load_f(data, t->type, t->nb, k, q, h);
                    gt_store_f(data, t->type, t->nb, k, q, h, v + g_press.bias);
                }
                g_press.applied = true;
            }
        }
    }
    gt_tensor_put(t, *buf, is_host);
}

bool gt_relied_cb(struct ggml_tensor * t, bool ask, void * user_data) {
    (void) user_data;
    if (t == nullptr) {
        return false;
    }
    const bool want_kq = g_press.armed || g_dial_mask.armed;
    const bool want_sm = g_relied.armed && !g_relied.skip;
    if (!want_kq && !want_sm) {
        return false;
    }
    const char * name = ggml_get_name(t);
    if (name == nullptr) {
        return false;
    }
    const bool is_kq = strncmp(name, "kq-", 3) == 0 && name[3] >= '0' && name[3] <= '9';
    const bool is_sm = strncmp(name, "kq_soft_max-", 12) == 0;
    if (is_kq && want_kq) {
        if (ask) {
            return true;
        }
        gt_mutate_kq(t, name);
        return true;
    }
    if (!is_sm || !want_sm) {
        return false;
    }
    if (ask) {
        return true;
    }
    g_relied.saw_softmax = true;
    const int layer = atoi(name + 12);
    const int64_t n_kv   = t->ne[0];
    const int64_t n_q    = t->ne[1];
    const int64_t n_head = t->ne[2];
    if (n_q != 1 || n_kv <= 0 || n_head <= 0) {
        return true;
    }
    g_relied.got_decode = true;

    bool is_host = false;
    const uint8_t * data = gt_tensor_bytes(t, g_relied.buf, &is_host);
    if (data == nullptr) {
        return true;
    }

    for (int h = 0; h < (int) n_head; ++h) {
        if (g_relied.headset.count({layer, h}) == 0) {
            continue;
        }
        for (size_t s = 0; s < g_relied.spans.size(); ++s) {
            int32_t a = g_relied.spans[s].start;
            int32_t b = g_relied.spans[s].end;
            if (a < 0) {
                a = 0;
            }
            if (b > (int32_t) n_kv) {
                b = (int32_t) n_kv;
            }
            if (a >= b) {
                continue;
            }
            double mass = 0.0;
            for (int32_t k = a; k < b; ++k) {
                mass += (double) gt_load_f(data, t->type, t->nb, k, 0, h);
            }
            g_relied.span_sum[s] += mass;
        }
    }
    return true;
}
