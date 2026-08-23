#pragma once

// RELIED hook: retrieval-head attention mass on named token spans.
// Fraction = mean over profiled heads and decode steps of the summed
// attention probability on the span's key positions.
// Never falls back to all-heads. Flash attention must be off or
// kq_soft_max tensors are absent.
//
// Press (PASTA-family): guarded additive bias on pre-softmax kq scores.
// No press params → the kq mutate does not run.
// Dial (CFG-family): a second last-token decode with span keys masked
// to -inf, then logit mix (1+α)·cond − α·masked. No dial params →
// that extra decode does not run.

#include "ggml.h"

#include <nlohmann/json.hpp>
#include <string>
#include <utility>
#include <vector>

using json = nlohmann::ordered_json;

struct gt_relied_span {
    std::string id;
    int32_t start = 0; // inclusive token index
    int32_t end   = 0; // exclusive
};

struct gt_relied_snapshot {
    json fractions = json::object(); // span id -> fraction
    int n_steps = 0;
    int n_heads = 0;
    bool saw_softmax = false;
};

void gt_relied_arm(
    const std::vector<std::pair<int,int>> & heads,
    const std::vector<gt_relied_span> & spans);

void gt_relied_disarm();

void gt_relied_finish_step();

gt_relied_snapshot gt_relied_take();

void gt_relied_pause();
void gt_relied_resume();

void gt_press_arm(
    const std::vector<std::pair<int,int>> & heads,
    const std::vector<gt_relied_span> & spans,
    float strength,
    int32_t n_prompt);

void gt_press_disarm();
bool gt_press_is_armed();
bool gt_press_applied();

void gt_dial_mask_arm(const std::vector<gt_relied_span> & spans);
void gt_dial_mask_disarm();
bool gt_dial_mask_applied();

void gt_dial_mix_logits(float * cond, const float * uncond, int n_vocab, float alpha);

bool gt_relied_cb(struct ggml_tensor * t, bool ask, void * user_data);
