Local AI program: an `--embed` mode that makes search vectors (triage search, part 6 of 8)

## What changes

`lastbook-llm`, the program that runs the local AI, can now also be started as `lastbook-llm --model FILE --embed`. It then
loads an embedding model (the search index's bge-small) instead of a writing one and makes vectors from text. Only
`packaging/llm/lastbook_llm.cpp` changes (+104 / -12), and `docs/TRIAGE-SEARCH.md` gets a short note in section 6.

- **Start:** `--embed` is a new option. The default context is 512 tokens for it (bge-small reads at most 512); `--ctx`
  still wins. The context is made with embeddings on and `[CLS]` pooling, and the batch size equals the context, so a text
  is read in one pass. `--cpu-only` and `--threads` work as before.
- **One request:** `{"op":"embed","id":1,"texts":["...","..."],"max_tokens":320}`. The answer is
  `{"ev":"embedding","id":1,"dim":384,"vectors":[[...],[...]],"n_tokens":[..],"ms":..}`: for each text the vector of its first
  token (`[CLS]`), scaled to length 1. A text longer than `max_tokens` is cut there, and the end mark is kept as the last
  token. A text that cannot be read, a request cancelled, or `texts` that are not strings give
  `{"ev":"error","id":1,"code":"encode|cancel|bad_request",...}`.
- **`ready`** says `"embed":true`, `"pooling":"cls"` and `"dim"`. A caller can tell a runner that embeds from an older one
  (which would just fail to start, or load a chat model) and can check what it is about to be given.
- `{"op":"quit"}` or the end of standard input still leave. The program still only talks through its standard input and
  output; it opens no socket and reads only the model file it is given.
- `tokenize()` takes an optional "add the model's own marks" flag. The chat path passes none, so nothing changes there.
- Without `--embed` the program behaves as before: same default context (16,384), same `ready`, and an `embed` request gets
  `{"ev":"error","code":"bad_request","msg":"unknown op"}`, as any other unknown op does today (and `gen` the same way
  under `--embed`).

No build script changes. It uses the llama.cpp functions the runner already builds against (tag b12032).

## Why

The proposal (#{ISSUE}, under #154) has a meaning check for urgent questions: the question's vector is compared with the
vectors of example sentences, so an emergency in everyday words ("he's out cold on the pavement") is also treated as
urgent. That needs a model that makes vectors, running next to the app, without a new library, a new download of a
runtime, or a network. The runner already has llama.cpp in it, and bge-small is the model the search index already uses,
so this adds one mode to the program that is already shipped and checked.

This pull request is only the runner. The Python that starts it and uses the vectors is the meaning check in part 7.

## How it relates to #168

#168 (a draft, open, not merged) adds an embed op to the same file, for a different reason: a Mac build has no
onnxruntime, so it uses the runner to make the index's vectors. The two agree on the main parts:

| | #168 | this PR |
|---|---|---|
| Option | `--embed` | `--embed` |
| Request | `{"op":"embed","id","texts","max_tokens"}` | the same |
| Answer | `{"ev":"embedding","id","dim","vectors","n_tokens","ms"}` | the same |
| `ready` | adds `pooling`, `dim` | adds `pooling`, `dim` (and `embed`) |
| Unit-length vectors, first-token text cut then marks put back | yes | yes |

They differ in these ways:

- **Batching.** #168 puts up to 64 texts through one pass, each its own sequence (`n_seq_max` 64, unified KV cache), for
  building an index of 337,000 passages. This one reads one text at a time, because it is used for one question per
  request. On the author's fork, 8, 32 or 128 texts to a request gave no gain (5.3 ms a text in all cases).
- **Pooling.** #168 reads it from the model file (`cls`, `mean` or `last`) and refuses a file with none. This one sets
  `[CLS]` in code, since the only model it is used with is bge-small. It still says `"pooling":"cls"` in `ready`.
- **Marks.** #168 finds the model's start and end marks once and puts them back after cutting. This one tokenizes with
  the marks and, when the text is too long, cuts it and puts the end mark (`[SEP]`) back as the last token. Same result for
  bge.
- **`ready`** here also says `"embed":true`, which the meaning check reads. #168 has no such field; it has `pooling` and
  `dim`.
- **Default context:** 512 here, 2,048 there (for the 64-text pass).

The wire is the same, so a caller written for #168 (`RunnerEmbedder` in its `retrieval.py`) can use this runner for one
text at a time, and the meaning check could use #168's runner by reading `pooling` instead of `embed`, which is a
one-line change. If #168 is merged first, this pull request would shrink to nothing but that one line in the meaning
check, and I would drop the C++ from it. If this goes first, #168 would be rebased onto it: it adds the batching, the
pooling from the file and the mark search as its own changes on top of this.

**This clashes with #168, and not only in the C++.** Both add an embed mode to the same runner, but with part 7 this
series runs a meaning-based model by default, on every question (the urgency check), while #168 proposes meaning-based
search as its own feature. Whichever goes in first shapes what the runner's embed mode is for, which model it loads and
whether it batches. I would rather settle that with #168's author than race it, and I'd like the maintainers to say
which goes first.

## How it was tested

- **Built on Linux from this branch.** `packaging/llm/build_llm_linux.sh` in a clean `debian:13-slim` container
  (llama.cpp b12032, every CPU variant and Vulkan): it builds.
- **Run against the author's fork's build, same container, same request.** Both started with
  `--model bge-small-en-v1.5-q8_0.gguf --embed --cpu-only --threads 2`, sent three texts in one request ("he is not
  breathing", "how do i boil an egg", "my toddler drank bleach and is throwing up"), then `{"op":"quit"}`:
  - this branch's `ready` says `"embed":true,"pooling":"cls","dim":384,"n_ctx":512`; its `embedding` event has
    `"dim":384`, three vectors and `n_tokens` [6, 8, 13];
  - the vectors are identical to the fork build's (largest difference 0.0), so the port changed nothing in what the
    model gives back; the only difference is the added fields;
  - both stop on `quit`.
- **Not built on Windows or macOS.** The Windows build needs the portable toolchain in
  `packaging/llm/build_llm_windows.sh` and was not run; the fork's Windows build of the same code is the one the
  numbers below come from.
- **Numbers on the author's fork** (its [`docs/FORK.md`](https://github.com/STAirye/lastbook/blob/fork/lightweight-gemma-no-us-maps/docs/FORK.md); measured with the meaning check in part 7 running on this
  runner): it loads in 0.2 s and stays at 66 MB private memory, with no video memory (`--cpu-only`: Vulkan is slower per
  question and stalls for seconds the first time a size is seen). 5.3 ms a question; batching gains nothing.
- **Python tests:** none touch the runner's protocol on `main` (no test starts `lastbook-llm`). Run one file at a time
  with `PYTHONUTF8=0`: `test_what_ships` (12) and `test_llm_local` (4) pass. Only a C++ file and a docs file changed.

## What it doesn't do

- **No caller.** Nothing in the app starts `--embed` yet. The meaning check (`engine/meaning_red.py`) is part 7.
- **No change to chat mode.** The chat path is the same code; `tokenize()` has one more default argument.
- **No batching** and **no pooling from the model file** (see #168 above).
- **No other embedding models.** It is set up and measured only for bge-small (`[CLS]`, 384 numbers). A model with another
  pooling would need #168's pooling check.
- **No build script, model or download change.** The bge-small GGUF the meaning check uses is part 7's.
- The fork's other runner changes (a sliding-window check for the person's own Gemma file) are not here.

Part 6 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR5}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/5-confidence...triage/6-runner-embed](https://github.com/STAirye/lastbook/compare/triage/5-confidence...triage/6-runner-embed).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
