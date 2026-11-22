// Smoke probe: can the runner's own libllama.dll (derived/llm/bin-win, unchanged) embed with a BERT GGUF?
//   probe MODEL BACKEND_DIR [cpu|gpu] [max_tokens]   then one text per line on stdin (\n inside a text written as \\n)
// Prints one line per text: n_tokens ms v0 v1 ... (unit [CLS] vector), or "ERR ...".
#include "llama.h"
#include "ggml-backend.h"
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

static void quiet(ggml_log_level lvl, const char * t, void *) { if (lvl >= GGML_LOG_LEVEL_WARN) fputs(t, stderr); }

int main(int argc, char ** argv) {
    if (argc < 3) { fprintf(stderr, "usage\n"); return 2; }
    const bool cpu = argc > 3 && std::string(argv[3]) == "cpu";
    const int limit = argc > 4 ? std::atoi(argv[4]) : 512;
    llama_log_set(quiet, nullptr);
    auto t0 = std::chrono::steady_clock::now();
    ggml_backend_load_all_from_path(argv[2]);
    llama_backend_init();
    llama_model_params mp = llama_model_default_params();
    static ggml_backend_dev_t none[1] = { nullptr };
    if (cpu) { mp.devices = none; mp.n_gpu_layers = 0; }
    llama_model * model = llama_model_load_from_file(argv[1], mp);
    if (!model) { printf("ERR load\n"); return 1; }
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = cp.n_batch = cp.n_ubatch = 512;
    cp.embeddings = true;
    cp.pooling_type = LLAMA_POOLING_TYPE_CLS;
    cp.n_threads = cp.n_threads_batch = 2;
    llama_context * ctx = llama_init_from_model(model, cp);
    if (!ctx) { printf("ERR ctx\n"); return 1; }
    const llama_vocab * vocab = llama_model_get_vocab(model);
    const int n_embd = llama_model_n_embd(model);
    double load_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    fprintf(stderr, "LOADED %.0f ms n_embd=%d\n", load_ms, n_embd);
    llama_batch batch = llama_batch_init(512, 0, 1);
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        std::string text;
        for (size_t i = 0; i < line.size(); i++) {
            if (line[i] == '\\' && i + 1 < line.size() && line[i + 1] == 'n') { text += '\n'; i++; } else text += line[i];
        }
        auto t1 = std::chrono::steady_clock::now();
        std::vector<llama_token> toks(text.size() + 8);
        int n = llama_tokenize(vocab, text.data(), (int) text.size(), toks.data(), (int) toks.size(), true, false);
        if (n < 0) { toks.resize(-n); n = llama_tokenize(vocab, text.data(), (int) text.size(), toks.data(), (int) toks.size(), true, false); }
        toks.resize(n > 0 ? n : 0);
        if ((int) toks.size() > limit) { toks.resize(limit); toks.back() = llama_vocab_sep(vocab); }
        batch.n_tokens = (int) toks.size();
        for (int i = 0; i < batch.n_tokens; i++) {
            batch.token[i] = toks[i]; batch.pos[i] = i; batch.n_seq_id[i] = 1; batch.seq_id[i][0] = 0; batch.logits[i] = 1;
        }
        llama_memory_clear(llama_get_memory(ctx), true);
        int rc = batch.n_tokens > 0 ? llama_encode(ctx, batch) : -99;
        const float * v = rc == 0 ? llama_get_embeddings_seq(ctx, 0) : nullptr;
        if (!v) { printf("ERR encode rc=%d n_tokens=%d\n", rc, batch.n_tokens); fflush(stdout); continue; }
        double s = 0; for (int i = 0; i < n_embd; i++) s += (double) v[i] * v[i];
        s = std::max(std::sqrt(s), 1e-9);
        double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t1).count();
        printf("%d %.3f", batch.n_tokens, ms);
        for (int i = 0; i < n_embd; i++) printf(" %.7g", v[i] / s);
        printf("\n"); fflush(stdout);
    }
    llama_batch_free(batch);
    llama_free(ctx); llama_model_free(model);
    return 0;
}
