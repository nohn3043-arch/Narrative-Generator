## A story has to make sense



# Logical Story Engine

> A writing tool that keeps your story consistent from beginning to end – no more plot holes or characters acting out of character.

## What does it do?

You give it a starting idea. It helps you write a full story where:
- Characters stay true to themselves (no sudden personality changes).
- The plot flows logically (no "wait, how did we get here?" moments).
- Past events are remembered (foreshadowing doesn't get lost).

## Who is it for?

- Writers who struggle with long‑form consistency.
- Screenwriters who need to track plot threads.
- Game developers who build narrative‑driven worlds.
- Anyone who wants to tell a story without breaking its own rules.

## How to use it

1. Clone the repository.
2. Install a few dependencies (Python 3.9+).
3. Run the engine with a simple text prompt:



python story_engine.py --seed "A young woman discovers her best friend has been lying to her for years."



4. The engine will generate a chapter‑by‑chapter outline, check every “because → so” step, and produce a story that holds together.

> **No technical background required.** The engine does the logic checking for you – you just review and edit the output.

## Example

**Input:**  
`Elena, a detective, finds a torn photo in her missing partner's drawer.`

**Output (short excerpt):**  
*“Elena stares at the photo. It was taken two days before he vanished. Her hand shakes – not from fear, but from the realisation that the person in the background is her own boss.”*

The engine ensures that later chapters never forget the photo, the boss's role, or Elena's emotional state.

## License

- **Free for personal / research use.**
- **Commercial use requires permission.**  
  Contact: `ai@nohnlins.com`

## Get started

```bash
git clone https://github.com/nohn3043-arch/logical-story-engine.git
cd logical-story-engine
pip install -r requirements.txt
python story_engine.py
```

Happy writing – without the headaches. ✍️

```