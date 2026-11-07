# Runtime specification — must be finalized before launch

The input runner requires Python 3.10+ and only the standard library. No model or
solver is bundled. Participants supply permitted offline model weights and code.

The organizer has NOT yet captured a real Kaggle runtime for this competition.
The following are launch configuration items, not claims about provisioned hardware:

| Setting | Status |
|---|---|
| Inference internet | Must be disabled in competition settings |
| Open-weight model limit | Up to 7B parameters per model, per published rule |
| CPU/GPU model and count | Organizer must select and verify |
| RAM/VRAM | Record from actual configured runtime |
| Total notebook runtime | Set after benchmarking the hidden workload |
| Python and package versions | Capture from actual configured runtime |
| Permitted external weights/packages | Organizer must finalize rules |

Before launch, replace this draft with verified settings and an environment
snapshot (`python --version`, `python -m pip freeze`, and accelerator details).
Pillow is needed to rebuild organizer images, not to read the problem JSON.
