The core product principle I’d use is:

> **The author creates the claims. The Oracle creates the pressure that makes those claims survive contact with reality.**

So whenever something is placed on the canvas—sentence, diagram, hypothesis, argument, assumption, citation, number, conclusion—it acquires an epistemic “life.”

I’d design the author experience around **three layers**:

**Canvas → Living Content → Socratic Oracle**

---

# 1. The Canvas itself

The canvas should feel more like a mixture of Notion + whiteboard + IDE + research notebook than a chatbot.

### Freeform objects

The author can place:

* Text
* Headings
* Claims
* Questions
* Hypotheses
* Arguments
* Evidence
* Citations
* Data
* Images
* Diagrams
* Equations
* Code
* Quotes
* Conclusions
* Decisions
* Assumptions

But the important distinction is that the system understands these as **different semantic objects**, not simply text blocks.

For example:

> “AI agents will replace 30% of marketing work.”

should become a **Claim**.

And:

> “Because agents are cheaper than humans.”

becomes an **Argument / Reason**.

And:

> “Gartner predicts…”

becomes **Evidence**.

That semantic structure is what allows the Oracle to come alive.

---

# 2. Every object becomes “alive”

This is probably the defining feature of the product.

When I add:

> “Remote work increases productivity.”

the block shouldn't just sit there.

It should immediately acquire invisible state such as:

**Claim**

* What exactly is “productivity”?
* For whom?
* Compared to what?
* Under what conditions?
* What evidence supports it?
* What would falsify it?
* Are there competing explanations?

But the Oracle **doesn't dump those questions onto the user immediately**.

Instead, it watches.

The canvas becomes a continuously evolving **knowledge graph of the author's thinking**.

---

# 3. The Oracle should behave like a Socratic mentor

The Oracle shouldn't answer:

> “Remote work increases productivity because studies X, Y and Z…”

Instead:

> “What would you accept as sufficient evidence that productivity actually increased?”

Then perhaps:

> “Would higher output necessarily mean higher productivity?”

Then:

> “What alternative explanation could produce the same observation?”

The Oracle progressively moves the author toward a conclusion.

That's the key product mechanic.

### Question types

The Oracle needs a rich repertoire of Socratic moves.

**Clarification**

> What exactly do you mean by “better”?

**Definition**

> How would you distinguish this from the claim you're making?

**Assumption detection**

> What must be true for this argument to work?

**Evidence**

> What observation would make you reconsider this?

**Counterexample**

> Can you think of a case where this doesn't hold?

**Alternative hypothesis**

> What else could explain the same result?

**Causal reasoning**

> Why do you believe A causes B rather than merely correlates with it?

**Scope**

> Is this true universally or only under specific conditions?

**Consistency**

> Does this claim conflict with anything else you've written?

**Steelman**

> What's the strongest version of the opposing argument?

**Falsification**

> What would prove you wrong?

**Implication**

> If this were true, what else should we expect to observe?

**First principles**

> What are you assuming without justification?

**Perspective**

> Would this still be true from the customer's perspective?

**Ethics**

> Who bears the cost if this assumption is wrong?

---

# 4. Don't make the Oracle always ask questions

This is important.

If the Oracle constantly interrupts, the canvas becomes exhausting.

Instead, it should understand **when to intervene**.

For example:

### Low uncertainty

> “Paris is the capital of France.”

Do nothing.

### Moderate uncertainty

> “Customers dislike complicated onboarding.”

Small indicator:

**Oracle noticed something worth examining.**

### High uncertainty

> “AI agents will eliminate 40% of software engineering jobs by 2030.”

Now the canvas might subtly illuminate the claim.

Perhaps a small symbol:

`◉ 3 unresolved assumptions`

Clicking it reveals the Socratic path.

---

# 5. The “pressure system”

I think this is one of the strongest features you could build.

Every important assertion gets a **truth pressure level**.

For example:

**Claim**

> Agentic AI will reduce marketing operating costs by 50%.

**Oracle state**

Confidence: unknown
Evidence: weak
Assumptions: 5
Contradictions: 1
Falsifiers: unknown

The Oracle doesn't tell the user whether the claim is true.

Instead it applies pressure.

---

# 6. Oracle Presence

Don't make the Oracle a traditional chat window.

That would destroy the magic.

Instead, give it a **presence inside the canvas**.

For example:

`◌ Oracle`

Hovering over an idea could reveal:

> “There is something unresolved here.”

Click:

> **What makes you believe this?**

The author responds directly into the canvas.

Now the exchange becomes part of the reasoning history.

---

# 7. The Oracle should remember the author's reasoning

This is critical.

Suppose early in the document the author says:

> “Users value convenience above privacy.”

Five pages later:

> “Users will reject our product because we collect behavioural data.”

The Oracle recognizes the tension.

Instead of saying:

> “These statements contradict.”

It asks:

> “Earlier you suggested convenience tends to outweigh privacy. What changed in your reasoning?”

That's much more powerful.

---

# 8. Assumption extraction

Authors often don't know they're making assumptions.

The system should continuously extract them.

Example:

> “We should build a SaaS product for hospitals.”

Oracle discovers:

**Hidden assumptions**

1. Hospitals are willing to buy.
2. They have the identified problem.
3. The problem is expensive.
4. Existing solutions are insufficient.
5. Procurement won't kill adoption.
6. Regulatory constraints are manageable.

The user can expand this into an **Assumption Map**.

---

# 9. Claim graph

Every major statement becomes a node.

Example:

```text
            AI adoption increases
                     │
                     ▼
              Marketing automation
                     │
            ┌────────┴────────┐
            ▼                 ▼
       Lower labour       Faster execution
           cost
            │
            ▼
      Higher margins
```

But beneath each node:

```text
Claim
 ├── Evidence
 ├── Assumptions
 ├── Dependencies
 ├── Counterarguments
 ├── Unknowns
 └── Falsifiers
```

The author can literally see **where their reasoning is strong or weak**.

---

# 10. Evidence shouldn't just be citations

The Oracle should classify evidence.

For example:

**Evidence**

> “Company X increased conversion by 18%.”

Oracle might ask:

> Is Company X representative of your target population?

Then classify:

**Direct evidence**
**Indirect evidence**
**Anecdotal evidence**
**Expert opinion**
**Experimental evidence**
**Statistical evidence**
**Mechanistic evidence**

This prevents the common mistake of treating every citation as equivalent.

---

# 11. “Challenge this idea”

The author should be able to summon opposition deliberately.

A button:

### Challenge

The Oracle temporarily becomes an adversary.

It might say:

> “Assume your thesis is wrong. Construct the strongest explanation for why.”

This can branch into an **Anti-Thesis branch**.

---

# 12. “Find the weakest link”

Another extremely useful command:

### Find weakest link

Oracle traverses the argument graph and identifies:

> “Your conclusion depends disproportionately on this assumption.”

But again, it doesn't solve it.

It asks:

> “What evidence would justify relying on this assumption?”

---

# 13. “Make me uncomfortable”

This could become a signature feature.

### Pressure test

The Oracle asks the hardest questions it can.

For example:

> “What would you have to believe for this entire thesis to be wrong?”

Then:

> “Which of those beliefs have you actually verified?”

---

# 14. Branching thought experiments

The canvas should support alternate universes.

For example:

**Scenario A**

> Assume the hypothesis is true.

**Scenario B**

> Assume it is false.

**Scenario C**

> Assume the opposite is true.

The author can explore each branch.

This is especially useful for:

* strategy
* science
* philosophy
* product design
* fiction
* research
* policy
* business planning

---

# 15. “What am I missing?”

A deceptively powerful command.

The Oracle shouldn't answer with a giant list.

Instead:

> “You've considered economic and technical consequences. Which consequence category haven't you examined?”

Then wait.

That's much closer to Socratic teaching.

---

# 16. Contradiction detection

The Oracle continuously watches the canvas.

Suppose:

> “Users want simplicity.”

Later:

> “We should introduce 14 configuration settings.”

Oracle quietly flags:

**Tension detected**

and asks:

> “How do these two ideas coexist?”

This becomes extremely valuable for long documents.

---

# 17. The “why ladder”

Sometimes an author gives an explanation but hasn't reached the underlying cause.

The Oracle can progressively drill down:

> Why?

> Because users don't trust AI.

> Why?

> Because they can't see what it did.

> Why does that matter?

> Because they can't distinguish mistakes from intended behaviour.

Eventually:

**Root issue discovered**

The author, rather than the AI, discovers the conclusion.

---

# 18. The Oracle should have multiple modes

Not personalities—**reasoning modes**.

For example:

### Socratic

Questions only.

### Adversarial

Try to break the argument.

### Scientific

Demand hypotheses, measurements and falsifiability.

### Philosophical

Explore definitions, assumptions and implications.

### Strategic

Challenge incentives, constraints and second-order effects.

### Editorial

Challenge clarity and coherence.

### Research

Challenge evidence quality.

### Ethical

Explore externalities and moral assumptions.

The author chooses the lens.

---

# 19. “Reveal the path”

This is where the product becomes magical.

The Oracle should maintain an invisible reasoning tree:

```text
Original claim
      ↓
Clarification
      ↓
Hidden assumption
      ↓
Counterexample
      ↓
Revised hypothesis
      ↓
New evidence
      ↓
Refined conclusion
```

The author can eventually click:

### Show my journey

And see how their thinking evolved.

That becomes extremely valuable for researchers, writers and students.

---

# 20. The Oracle should distinguish knowing from believing

This is fundamental.

Every claim can have epistemic status:

**Observed**

**Measured**

**Derived**

**Inferred**

**Hypothesized**

**Assumed**

**Believed**

**Unknown**

The author can see:

> **What do I actually know?**

versus

> **What am I merely assuming?**

That could become one of the product's killer features.

---

# 21. “Epistemic heatmap”

Imagine the canvas visually changing based on epistemic strength.

For example:

```text
GREEN     well-supported
YELLOW    assumption-heavy
ORANGE    weak evidence
RED       contradiction / unsupported
GREY      unknown
```

Not necessarily literal colours—you could use subtle visual texture/glow.

The document effectively becomes a **map of certainty and uncertainty**.

---

# 22. The Oracle should know when NOT to interfere

This is just as important as intervention.

The system should learn:

> “The author is brainstorming.”

Don't interrupt.

Later:

> “The author is forming a conclusion.”

Increase pressure.

Later:

> “The author is writing the final argument.”

Switch to verification mode.

So the Oracle needs awareness of **author intent and cognitive state**.

---

# 23. Intent declaration

At the beginning of a canvas:

> **What are you trying to discover?**

Examples:

**Understand a problem**

**Develop a theory**

**Make a decision**

**Write an argument**

**Research a topic**

**Solve a problem**

**Design something**

**Understand myself**

That changes how the Oracle behaves.

---

# 24. The author should control the Oracle's aggressiveness

Something like:

```text
Oracle pressure

○ Silent observer
○ Gentle mentor
● Socratic
○ Challenger
○ Ruthless
```

And perhaps:

**Interrupt me:** Rarely / Occasionally / Frequently

---

# 25. “Hold the answer”

This should literally be a product feature.

The author could specify:

> **Don't tell me the answer.**

The Oracle then becomes contractually constrained to:

* ask questions
* provide counterexamples
* expose assumptions
* suggest experiments
* present competing hypotheses

But never reveal the conclusion.

You could even have:

### Reveal answer

locked behind a deliberate action.

That's useful for education.

---

# 26. Progressive revelation

The Oracle shouldn't dump all possible questions simultaneously.

It should choose the **next most valuable question**.

This creates a dialogue:

```text
Author:
Remote work improves productivity.

Oracle:
What do you mean by productivity?

Author:
More work completed per employee.

Oracle:
Would completing more work necessarily mean
employees became more productive?

Author:
Not necessarily.

Oracle:
What else could explain the increase?
```

Each question changes the state of the investigation.

That interaction is the heart of the product.

---

# 27. “Dead ends”

The Oracle should recognize when an investigation isn't progressing.

It could gently ask:

> “We've examined this assumption from four directions without gaining new information. What observation could actually resolve it?”

This prevents endless philosophical questioning.

---

# 28. Experiments instead of answers

One of the most important capabilities.

Instead of:

> “Your assumption is probably wrong.”

Oracle:

> “What experiment could distinguish the two explanations?”

That converts philosophy into action.

For example:

**Hypothesis**

> Customers don't buy because pricing is too high.

Oracle:

> “What evidence would distinguish price sensitivity from lack of perceived value?”

Now the author might design:

> A/B test.

The Oracle has moved the author from belief → investigation.

---

# 29. Decision nodes

Eventually the author needs to stop thinking.

The canvas should allow:

### Decision

> Build MVP for enterprise customers.

The Oracle checks:

> What assumptions remain unresolved?

The author can explicitly say:

**Accept uncertainty.**

Now the decision becomes:

```text
Decision
├── Evidence
├── Reasoning
├── Known risks
├── Accepted uncertainties
└── Revisit when...
```

That's incredibly useful.

---

# 30. Time-aware reasoning

The Oracle should remember:

> “You decided X three months ago because of assumptions A, B and C.”

Later:

> “Assumption B is no longer true.”

It asks:

> “Does your original decision still stand?”

Now the canvas becomes a **living reasoning system**, rather than a static document.

---

# 31. Multiple perspectives

For complex questions, let the author spawn perspectives:

```text
My perspective
Customer
Competitor
Scientist
Engineer
Investor
Regulator
Ethicist
Sceptic
```

But again, these aren't chatbots giving answers.

Each perspective asks **different questions**.

---

# 32. The author should be able to talk directly to any object

This UX could be fantastic.

Click a paragraph:

> **Ask this idea**

Click a claim:

> **Challenge this**

Click an assumption:

> **Explore**

Click evidence:

> **Assess reliability**

Click a conclusion:

> **Try to break it**

Click empty canvas:

> **What should I investigate next?**

This avoids a generic chat interface altogether.

---

# 33. Oracle annotations

Tiny annotations around the canvas:

```text
⚠ Assumption
? Undefined term
↔ Contradiction
◇ Weak evidence
! High-impact uncertainty
→ Causal leap
∴ Unsupported conclusion
```

The author can navigate the document through these.

---

# 34. A “truth frontier”

This could be the conceptual centrepiece.

The Oracle maintains:

> **What you know**
> **What you think**
> **What you don't know**
> **What could be known**
> **What cannot currently be known**

The author is essentially navigating the boundary between knowledge and ignorance.

That's much deeper than an AI assistant.

---

# 35. The most important screen might be this

Imagine the author opens the canvas and sees:

```text
                 YOUR THESIS

       ┌──────────────────────────────┐
       │ AI agents will transform     │
       │ marketing operations.        │
       └──────────────┬───────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Evidence    Assumptions   Counterclaims
         7             9             4
          │           │
          │       ⚠ 3 unresolved
          │
          ▼
       UNKNOWN
          │
          ▼
   "What observation would
    change your mind?"
```

And the author responds directly on the canvas.

That's the magic.

---

# 36. The MVP I'd actually build

I'd resist building everything above.

The first version should probably have only **seven primitives**:

### 1. Living blocks

Every text block is semantically classified automatically.

### 2. Oracle presence

A subtle indicator appears when an idea needs examination.

### 3. Socratic questioning

The Oracle asks exactly one high-value question at a time.

### 4. Assumption detection

Extract hidden assumptions behind claims.

### 5. Counterargument generation

Generate competing explanations without declaring which is correct.

### 6. Reasoning graph

Visualize claim → evidence → assumption → conclusion relationships.

### 7. Epistemic state

Show:

**Known / Supported / Inferred / Assumed / Unknown**

That alone could already feel radically different from ChatGPT.

---

# 37. And there is one deeper feature I'd seriously consider

### **The Oracle refuses premature closure.**

Humans naturally want conclusions.

The author writes:

> “Therefore X is true.”

Oracle doesn't say:

> “Correct.”

It asks:

> “What has been established strongly enough that ‘therefore’ is justified?”

That's the philosophical engine.

The product is not trying to **increase the amount of information inside the author's head**.

It's trying to **increase the quality of the author's beliefs**.

---

## The product in one sentence

I would frame the entire thing as:

> **A living canvas where ideas become questions, assumptions become visible, arguments become testable, and conclusions have to earn their way into existence.**

And I think the really interesting product question isn't actually **“How intelligent can the Oracle be?”**

Assuming infinite knowledge, the harder and more valuable question is:

> **“What is the smallest intervention the Oracle can make that causes the author to discover something they could not see before?”**

That should probably become the central design principle for the whole system.
