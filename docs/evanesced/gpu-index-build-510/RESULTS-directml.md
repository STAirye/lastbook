# DirectML measurement (2026-11-27)

onnxruntime-directml 1.24.4 (private install in ./ortdml, global packages untouched), same fp32 model.onnx and
tokenizer as the app, the same 3,000 passages as the Vulkan run (ids.npy, every 112th active chunk of the Medium
pack's index). Reference: v_ortcpu.npy (onnxruntime CPU). GPU: RTX 3080 Ti, so this is DirectML on an NVIDIA card,
not yet measured on AMD or Intel. Script: dml.py.

| Route | Passages/s | Lowest cosine vs CPU | Max abs diff |
|---|---|---|---|
| onnxruntime CPU | 20 | | |
| runner Vulkan (q8_0, 64/request) | 188 | 0.999868 | |
| DirectML, batch 16 | 242 | 0.9999998 | |
| DirectML, batch 48 | 320 | 0.9999998 | 3.3e-7 |
| DirectML, batch 128 | 356 | 0.9999998 | |
| onnxruntime CUDA (batch 48) | 629 | 0.9999998 | 1.4e-4 |

- Top-10 neighbour overlap within the 3,000: 100 %; nearest the same: 100 %.
- No row bit-identical to the CPU (so it really ran on the GPU); differences are float32 rounding.
- Estimated model step for 338,910 passages: about 18 min at batch 48, 16 min at 128 (CUDA measured 11 min,
  CPU 3.6 h). Whole build about 1 h 10 min (the other 55 min unchanged). Estimate, not a timed build.
- Needs SessionOptions enable_mem_pattern=False and sequential execution.
- Limits: Windows only; onnxruntime-directml and onnxruntime-gpu both install the `onnxruntime` module, so one
  environment has one or the other.
