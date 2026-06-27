# 🧬 DNA — SuneelWorkSpace Organ

## Purpose
Defines stylistic guidelines and logs accept/reject feedback.

## What\s Inside
* `identity/`: Suneel profile tone parameters and prompt evaluations.
* `feedback/`: Accept/Reject loop.

## Key Files
* [dna/identity/prompts/identity_prompt.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/prompts/identity_prompt.md): Main behavior prompt.
* [dna/identity/profile/tone_profile.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/profile/tone_profile.md): Suneel voice definition.
* [dna/identity/adaptive/adaptive_identity.py](file:///Users/MAC/SuneelWorkSpace/dna/identity/adaptive/adaptive_identity.py): Profile modifier.

## Provides (to other organs)
* Behavioral prompt files and identity alignment rules.

## Needs (from other organs)
* Vector searches from `brain`.
* Safety limits from `skeleton`.

## CLI Commands
* `prompt-eval`: Evaluates system prompts.
* `prompt-new`: Increments prompt version.
* `identity-accept`: Learns accept patterns.
* `identity-reject`: Logs style rejections constraints.

## How To Add Something Here
1. Put new prompt iterations in `dna/identity/prompts/versions/`.
2. Run evaluations using prompt-eval.
