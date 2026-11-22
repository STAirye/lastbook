Title: Local AI start: "ready" hides the load wait, and a load over 10 minutes fails every time

## What happens

Before the first question, Chat's status line says **"Local AI ready · it starts when you ask"** (`web/chat.js`, the
`stopped` state; Settings says "ready; it starts when you ask and stops after 15 minutes unused", `web/app.js`). The
model really is loaded only when the first question is sent, so that first answer waits for it.

On a fast desktop (Ryzen 7 5800X3D, 32 GB, RTX 3080 Ti, a 6.3 GB Gemma 4 E4B file) the load took **24 seconds**
(`load_ms: 22823` in the runner's ready line) before anything else happened. A mid-range laptop, a CPU-only machine or
a larger model file will take longer: likely over a minute, and several minutes on low-end hardware (estimated, not
measured). After 15 minutes unused it stops, and the next question waits again.

The answer area does show "Starting the local AI… N%" while it loads, so nothing is broken. The problem is the
expectation: "ready" reads as "answers right away", and someone in a hurry gets a long pause they weren't warned about.
In an emergency they may give up and look elsewhere.

## On slow machines it can fail every time

There is also a hard limit on the load itself: `START_WAIT = 600` in `llm_local.py`, with no setting or environment
variable. If the model isn't ready 10 minutes after a question starts waiting, the half-loaded runner is killed and the
answer says "The local AI took too long to start." The next question starts the load from zero and hits the same
limit. So on a machine that needs more than 10 minutes (a large file on a slow hard disk, or too little free memory so
it swaps), the local AI never works, and nothing tells the person it's because the machine is slow rather than broken.
The fit check looks at memory, not at disk or CPU speed, so it can't warn about this beforehand. (A second question
asked during the load joins it with its own 10-minute clock, but the first one's timeout kills the runner for both.)

The 15-minute idle stop (`IDLE_STOP`, changeable only with `LASTBOOK_AI_IDLE_S`) can't interrupt a load: it starts
counting when the model reports ready, and only stops a model that is ready and not answering.

## Possible directions (for the maintainers to choose)

- **Say what will happen**, e.g. "Local AI ready · the first answer takes a little longer while it starts", or with an
  estimate from the model's size and this computer's memory and GPU, which the app already measures for its fit check.
- **Start loading earlier**: when Chat is opened, or when the person starts typing, so the load overlaps with writing
  the question. That uses memory before it's needed, which matters on smaller machines.
- **Both**: warn, and start early only where the fit check says there's room.
- **For the 10-minute limit:** don't kill a load that is still making progress (the runner reports its percentage), or
  remember how long the last load took and say so ("this computer took 12 minutes last time"), or let the load finish in
  the background even after the waiting question gives up, so the next one finds it ready.

I can make the change once there's a preferred direction.

(I used an AI assistant to help write this up.)
