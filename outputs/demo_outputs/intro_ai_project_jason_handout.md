% Calibration handout — Jason
% Build an AI-Powered Application

**Annotator:** Jason

**Brief:** Design and implement an original AI application that applies one or more techniques
from the course (computer vision, NLP, deep learning, structured prediction) to a real-world
problem. The system must go beyond a tutorial re-implementation: it should address a genuine
user need, demonstrate working inference on real inputs, and include a written reflection on
limitations and failure cases. Deliverables: working demo on real-world inputs, at least one
trained or fine-tuned model component, written reflection on limitations and ethics, and
reproducible code + model weights.

**Deadline:** 30 days

**Rate each plan:** Feasibility 1–5 (1 = not viable, 5 = clearly doable in 30 days) |
Scope fit 1–5 (1 = wrong size for the assignment, 5 = perfectly scoped) | One sentence of notes.

\bigskip

---

**Plan 1:** YOLO-based hand exercise assistant — rep counting + form checking for hand rehabilitation

The student builds a real-time computer vision application that uses a pre-trained YOLO hand
keypoint model (e.g., YOLOv8-pose with hand landmark detection, or MediaPipe Hands) to track
finger and wrist keypoints from webcam video and provide live feedback on hand rehabilitation
exercises. The core mechanism runs keypoint detection frame-by-frame, computes finger extension
or grip angles, and fires a rep counter when the joint angle crosses a threshold indicative of
full movement completion (e.g., full fist close and open). The two scenarios being compared are:
(1) a rep-counting-only mode that tracks completion of a hand movement cycle, and (2) a
form-feedback mode that flags incomplete range of motion or asymmetric finger movement and
prompts the user to correct it. The deliverable is a live demo on webcam footage with a
real-time overlay showing hand keypoints, joint angles, rep count, and form warnings. The
reflection addresses failure cases (occluded fingers, skin tone variance, proximity to camera)
and the risk of providing incorrect guidance in a medical rehabilitation context.

Feasibility: 5 / 5 \quad Scope fit: 5 / 5

Notes: Exhibits both theoretical and engineering problem solving, perfectly scoped.

\medskip

---

**Plan 2:** Pothole severity classification from road images

The student builds a system that not only detects potholes in road images but classifies each
detected pothole by severity (e.g., minor surface crack, moderate depression, severe structural
damage) to help prioritize road maintenance. The core mechanism uses a computer vision model
trained on a labeled pothole dataset to output both a localization (bounding box or segmentation
mask) and a severity class per pothole. The two scenarios being compared are: (1) detection-only
output that flags pothole presence, against (2) severity-aware output that ranks detected
potholes so maintenance crews can triage the most dangerous ones first. The deliverable is an
inference demo on held-out road images with severity labels overlaid, a confusion matrix across
severity classes, and a reflection on annotation subjectivity (human raters may disagree on
severity boundaries), dataset bias (most public datasets lack severity labels and come from
limited geographies), and the downstream risk of under-prioritizing a severe pothole due to
model error.

Feasibility: 4 / 5 \quad Scope fit: 3 / 5

Notes: Large amount of manual labour for annotating the severity of potholes in the dataset, a simple classifier so not much that technical knowledge gained from this. Could have done more.

\medskip

---

**Plan 3:** Tree-LSTM for structured text understanding

The student implements a Tree-LSTM (Tai et al. 2015) that encodes the syntactic parse tree
of a sentence into a fixed-size vector, and applies it to a sentiment analysis or natural
language inference task (e.g., Stanford Sentiment Treebank or SNLI). The core mechanism is
a recursive neural network that computes hidden states bottom-up over a dependency or
constituency parse tree rather than left-to-right over a token sequence, allowing the model
to capture long-range syntactic relationships. The two scenarios compare a flat sequential
LSTM baseline against the Tree-LSTM, measuring whether hierarchical encoding improves
performance on examples where meaning depends on sentence structure (e.g., negation scope,
comparative constructions). The deliverable includes a working PyTorch implementation,
train/validation/test split results, attention-visualization or tree-rendering of a few
examples, and a reflection on why the Tree-LSTM may or may not outperform the sequential
baseline on the chosen dataset.

Feasibility: 3 / 5 \quad Scope fit: 4 / 5

Notes: Novel design, but computationally infeasible and also too much to implement for a 30 day project. 

\medskip

---

**Plan 4:** Adaptive AAC (Augmentative and Alternative Communication) board for non-verbal users

The student builds an AI-powered symbol communication board for non-verbal individuals. The
core mechanism uses a language model (e.g., a fine-tuned GPT-2 or a retrieval-based symbol
predictor) to suggest the next most likely symbol or word given the user's selection history,
reducing the number of taps needed to construct a message. The two scenarios compare: (1) a
frequency-based baseline that ranks symbols by overall usage frequency, against (2) a
context-aware model that updates its predictions based on the current partial message and
user history. The deliverable is a browser or desktop UI where a user can tap symbols to
build sentences, with the model reordering the board in real time, plus a user study or
simulation showing average message-construction time and click count under both conditions.
The reflection addresses accessibility risk (a wrong prediction is more disruptive for a
non-verbal user than for a typical autocomplete user), data sparsity (individual AAC users
have highly personalized vocabularies), and the ethical obligation to validate with actual
users or domain experts rather than simulated proxies.

Feasibility: 5 / 5 \quad Scope fit: 4 / 5

Notes: Pretty cool idea, even though its kind of just an LLM wrapper, but its tricky to evaluate.

\medskip

---

*Thank you for your time. Your ratings will be used to calibrate the consultant agent's
scope_fit predictions for intro-level AI course projects.*
