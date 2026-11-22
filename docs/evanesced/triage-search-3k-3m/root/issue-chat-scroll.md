## ISSUE

Title: Chat scrolls past the answer to the source cards when the answer finishes

### What happens

While an answer is written, Chat keeps the view at the bottom of the page. When the answer finishes, the full source
cards (with excerpts) are drawn **below** the answer, and Chat scrolls to the bottom again. So the person ends up
looking at the source cards, and the answer they waited for is above the top of the screen. They have to scroll up to
read it, every time.

Measured in the browser at 1280×800 with a 14-line answer and 8 sources: when the answer finished, the page was
scrolled to its very end (931 px), and the answer's last line was 339 px **above** the top of the window. None of the
answer was visible.

### Where

`web/chat.js`, `send()`: the redraw on every streamed event and the final redraw both call `scrollEnd()`, which
scrolls to `document.body.scrollHeight`, the end of the page, not the end of the answer. The more sources are drawn
after the answer (encyclopedia articles, places), the further it scrolls away.

### Expected

The answer stays in view when it finishes; the sources are below it, a scroll away.

(I used an AI assistant to help write this up.)

---

## PR

Title: Chat: keep the answer in view when it finishes, instead of scrolling to the sources

Fixes #<issue>.

### What changes

While an answer is written, the view now follows **the end of the answer**, not the end of the page. When it
finishes, the answer stays where it is, and the source cards are below it.

- A short answer stays whole on the screen; the cards start below it.
- A long answer keeps its last line just above the question box, as it does while it's written.
- If the person scrolls away while the answer is written (up to reread, or down to the cards), the view no longer
  pulls them back, unless the answer's end is still in view.

Only `web/chat.js` changes (and its `?v=` in `index.html`): `send()` follows the answer with two small helpers
(`follow`, `following`) instead of `scrollEnd()`. Opening a chat and sending a question still scroll as before.

### How it was tested

In the browser at 1280×800, with a simulated streamed answer and 8 sources (a stubbed `/api/chat`, so it's exact and
repeatable):

| | Before | After |
|---|---|---|
| 14-line answer, when it finishes | the answer is entirely above the window (its end at −339 px) | the whole answer is visible (top 96 px, end 542 px; the question box at 655 px) |
| 40-line answer, second question in the chat | (same: the page's end) | its last line just above the question box (543 px) |
| scrolled to the top while the answer is written | pulled back to the end | stays at the top |

Not yet tried with a real model's answer. `app/tests/test_chat_steps.py` and `test_chat_tables.py` pass.

(I used an AI assistant to help write this up.)
