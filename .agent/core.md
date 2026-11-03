---
name: core
description: Global coding ruleset — applies to EVERY project, EVERY language, EVERY agent. This is the only file loaded automatically; it tells the agent how to detect and take in the T1_ (language/engine) and T2_ (project) files the user supplies.
updated: 2026-10-13
---

# UNIVERSAL CODING STANDARDS

> This file is **global**, not tied to any project. It never contains the syntax of a specific
> language (that belongs in `T1_`) or the features of a specific project (that belongs in `T2_`).
> Language/framework syntax and lifecycle belong in T1_; business features belong in T2_.

---

## Reading order

Startup and clarification → planning and scope → architecture → files and naming → clean code → CRUD and REST APIs → validation → debugging → delivery and commits.

The rules apply throughout the task; their position indicates the primary stage where they are used.

---

## 0. TIER CHECK — DO THIS BEFORE WRITING ANY LINE OF CODE

**Only this file loads automatically.** The two lower tiers are supplied by the user: as an
attached file, pasted content, or a file sitting in the project directory. The agent must
**never** go hunting for them at a fixed path.

| Tier | Prefix | Contents | Example |
|---|---|---|---|
| Global | *(none)* | this file | `core.md` |
| Language / Project Type | `T1_` | conventions for one language in one project type/framework | `T1_lua-pz-mod.md` |
| Project | `T2_` | what one specific project is supposed to do | `T2_bot-dc-pz-server.md` |

### 0.1 Mandatory startup procedure

1. Read this entire file and confirm you understand every section.
2. **Check for `T1_`**: is there a rules file matching BOTH the language and the project type/framework?
   It counts as present if the file is attached, pasted in, or located in the project directory.
3. **Check for `T2_`**: same, for the project specification file.
4. **If missing** → emit the warning in 0.3 **once**, then **continue working** with this file alone.
5. Reload this file when switching to a new module/file, and when switching to a different project.

Do not stop and wait for a file. A missing tier is normal — just **say so** and **do not invent**
what that tier was supposed to define.

### 0.2 Select an exact T1 profile

A T1 targets ONE language in ONE project type/framework. Detect candidates from the
project's dependencies and structure, then confirm the scope written in that file.
A language extension alone is insufficient: a Python script is not a Discord bot,
and TypeScript alone does not identify React, an HTTP API, a bot, or a CLI.

- Use only profiles supplied in the session/project; never assume an unseen profile exists.
- A specialized profile may explicitly extend a shared language profile. Load both;
  report a missing dependency rather than treating it as implicitly available.
- Priority within T1: the specialized profile overrides a specifically named rule of
  its declared base; T2 still has priority, and unrelated profiles never apply.
- Multi-stack projects need the matching profile for each stack being edited.
- When evidence does not identify the project type, ask only about that missing context.

### 0.2.1 Ownership of rules

| core — all projects | T1 — language + development context | T2 — one project |
|---|---|---|
| Meaningful names, coherent responsibilities, dependency boundaries | Identifier casing, import-compatible filenames, header syntax | Domain vocabulary and actual modules |
| Input validation, safe errors, lifecycle cleanup, secret redaction | Callback signatures, async/runtime behavior, serialization, adapters | Permissions, error catalog, storage/delete policy |
| Conditional CRUD/HTTP principles | ORM/routing/middleware, engine/bot lifecycle | Schema, endpoints, auth mechanism, pagination/limits |
| General testing/debugging and delivery workflow | Runner, linter, debugger/profiler, framework fixtures | Acceptance cases and release targets |
| Version changes only on request | Locations and tools for version metadata | Actual version values |

Do not copy core paragraphs into T1. Reference the core rule and add only concrete
implementation, a format-required exemption, or an explicit override. A T1 may retain
stack-specific checklist items; common checks remain in core section 9.2.

### 0.3 Warning template for a missing tier

Emit **once** at the top of the first reply of a task; do not repeat it on later turns.
If both are present, print nothing at all.

```
⚠ Missing tier:
- T1_<stack>: not provided → falling back to core's general conventions.
- T2_<project>: not provided → project spec unknown; I will ask rather than assume.
Send the file if you want me to follow your exact standard.
```

### 0.4 Behaviour when `T1_` is missing

- Use the rules in this file, applied through the most common idiom of that language.
- **Do not invent** custom conventions for that stack: no made-up namespace prefix,
  no invented file-naming pattern, no fabricated "standard" directory tree.
- Where a convention must be chosen and this file does not decide it → **ask** ([0.8], section 1).
  Do not choose it silently, and do not proceed on it as an assumption.

### 0.5 Behaviour when `T2_` is missing

- **Do not invent features.** Implement exactly what the user asked for in their message.
- Do not infer business behaviour from file names or variable names.
- If a business decision is required and there is no basis for it → **ask**. Do not decide on the user's behalf.

### 0.6 Conflict precedence

`T2_` > `T1_` > `core`.

The project file and the language file are an **addition**, not a replacement: they may add detail
or override **one specifically named rule**, but everything not explicitly overridden still applies.

Every time a rule is overridden, write one line in the output's `Notes`:
`Override: <rule overridden> — per <file name>, section <number>.`

### 0.7 When the user sends a tier file mid-task

Apply it starting from the very next reply. If the new file conflicts with code already produced,
state exactly what is off-standard and propose the fix — do not silently ignore it, and do not
rewrite everything on your own initiative before the user agrees.

### 0.8 Ambiguity → ask, never decide

If a request, a rule, or a design choice has more than one reasonable reading and the readings would
produce different code or behaviour, **ask the user**. Do not pick one on their behalf and do not
proceed on a guess. Only the ambiguous part waits — section 1.2 defines what counts as ambiguous,
how to ask, and what may continue in the meantime.


## 1. WHEN UNSURE

Two kinds of "unsure" — handled differently.

### 1.1 Technical unsureness — look it up first

How an API behaves, what a function is called, what the platform does. These have a factual answer.

Lookup order: **official documentation → how the original/vanilla implementation does it → the most stable and maintainable solution**.

Still unsure → **ask the user**. Do not guess at APIs, do not invent function names, do not assume
platform behaviour. Saying "I am not certain about X" beats delivering wrong code confidently.

### 1.2 Ambiguity — ask; do not look it up, do not decide

Something is **ambiguous** when it has more than one reasonable reading **and** the readings lead to
different code or behaviour — or when a decision is needed that the user, `T2_`, and this file have
not made. Lookup cannot settle it, because it is the user's decision. **Ask.**

Cases that must be asked (unless the request or `T2_` already answers them):

- Hard or Soft Delete ([2.3])
- a convention that neither this file nor a supplied `T1_` defines ([0.4])
- a business rule with no basis in `T2_` ([0.5])
- whether to clean up code noticed while editing ([2.4])

**How to ask**

- Say what is ambiguous, and list the options you see so the user can answer briefly.
- Ask about everything unclear in one message, not one question per turn.
- Never ask what the request, `T2_`, or this file already answers.
- A question must stay a question. "I will do X unless you object" is a decision, not a question.

**While waiting**

- The ambiguous part is **never implemented** before the user answers.
- Stop only what the ambiguity blocks: parts that depend on the answer wait; parts that do not
  depend on it continue.
- Say plainly at the top of the reply which part is waiting, and why.



---

## 2. PLANNING & CHANGE SCOPE

1. **Analyze** — file type, platform version, blast radius, dependencies.
2. **Design** — architecture, file list, data flow, extension points.
3. **Generate** — produce code following `core` + `T1_` + `T2_`.
4. **Validate** — run the checklist in section 9.2.
5. **Deliver** — file structure + code + testing guide + changelog.

For small edits (< 20 lines, 1 file) steps 2 and 5 may be condensed. Never jump from 1 straight to 3.

### 2.1 Stay in scope

Only modify the file/module explicitly requested. **Do not modify surrounding files on your own initiative.**

The one exception: deleting replaced code that nothing calls any more ([2.4]).

### 2.2 Preserve functionality

Keep existing, working core features intact. Unused or dead code is handled by [2.4].
Do not add features outside the original request.

### 2.3 Propose optimizations, don't force them

If you spot a better architecture, explain it clearly (reasoning + pros/cons).
**Wait for user confirmation** before refactoring. Never refactor without explicit permission.

### 2.4 Boy Scout Rule

While editing a file, if you notice outdated/meaningless variable names, or functions that are too
long or violate the rules above → **do not clean it up on your own.** Tell the user what you noticed
and **ask** whether to clean it up in this pass ([0.8]). Edit only after they say yes.
The goal is unchanged — the codebase gets cleaner every time the agent touches it — but the user
decides.

**Exception — replaced code.** When the requested change replaces a specific existing function or
feature with a new one, delete the code it replaces as part of the same change; no need to ask.
Keep it only if the user said to keep it.

- This covers only the code being replaced — other unused code you happen to notice falls under the
  dead-code rule below.
- **Code inside a comment is never deleted** — in any file, including the file you are editing.
- In other files ([2.1]): delete the replaced code only if it is live code and nothing calls it any
  more. If anything still calls it, do not delete it — ask ([0.8]).

**Dead code — comment it out, never delete it.** In the file you are already editing, if you can
**prove** that code is unused or dead, comment it out on your own instead of asking, and tell the
user. Deleting it is then the user's decision.

- **Proof** means: nothing calls or references it — no caller in the project, no dynamic, string-based,
  reflection, event-registration, or serialization reference, and it is not part of an exported or
  public API. State the evidence when you report it.
- Cannot prove it → do not touch it; ask as described above ([0.8]).
- Comment it out with the language's comment syntax, plus one comment giving the reason ([5.4]).
- Report every piece of code commented out this way in `Notes & Maintenance`: what, where, and the proof.

> 2.3 and 2.4 do not conflict: **2.4 applies to the file you are already editing** (list what you
> noticed, ask once, tidy in place after a yes); **2.3 applies to architectural changes** or to other
> files (explain with reasoning + pros/cons, wait for confirmation).

### 2.5 Keep each change focused

One change set = one clearly stated purpose. Never bundle a new feature, a refactor of an old
service, a schema migration, and a UI tweak into the same delivery.

- If describing the change needs the word "and", it is probably two changes.
- Split them so each one can be reviewed, tested, and **rolled back independently**.
- Where a refactor is genuinely needed to enable a feature, deliver the refactor first, on its own,
  with behaviour unchanged — then the feature on top.
- State the purpose of the change set in `Changelog`. A change that cannot be described in one
  sentence has not been scoped yet.

This is the delivery-level form of [2.1] stay in scope.

### 2.6 Version policy

- **By default, DO NOT touch version numbers**, even when editing many files in the same project.
  No automatic sync, no automatic bump.
- Only bump when the user explicitly asks ("bump version", "go to 1.2.0", …).
- Once bumping: **every location holding a version must be synced at the same time**, even if the
  user only asked to change one of them. `T1_` and `T2_` list what "every location" means for that stack/project.
- Never leave version numbers mismatched between files.



---

## 3. ARCHITECTURE & SOLID PRINCIPLES

| | Principle | Requirement |
|---|---|---|
| **S** | Single Responsibility | Each Class/File/Function holds exactly ONE responsibility. Doing several jobs → split it immediately. |
| **O** | Open / Closed | Open for extension with new features. Closed for modification of stable, already-working code. |
| **L** | Liskov Substitution | A subclass must be fully substitutable for its parent without breaking the program. |
| **I** | Interface Segregation | Many small, specific interfaces over one do-everything interface. Never force a class to implement methods it will never use. |
| **D** | Dependency Inversion | High-level modules must not depend directly on low-level ones — both depend on abstractions. Do not hardcode concrete dependencies. |

### 3.1 Keep external systems behind a boundary

Anything you do not control — third-party APIs, vendor SDKs, other teams' services, the game engine's
own data structures — must not leak its shape into the rest of the application.

- Translate the foreign structure into your own type **at exactly one place**: the boundary.
- Nothing past that boundary ever touches the vendor's field names, status codes, or payload shape.
- When the external service changes, exactly one file changes.

```
// CORRECT — one translation point
// Ranh gioi: doi payload cua nha cung cap sang kieu cua minh
function toPaymentReceipt(vendorResponse) { ... }   // called once, at the edge

// WRONG — vendor shape spreads everywhere
if (response.data.attributes.txn_status === "OK_2") { ... }   // repeated in 9 files
```

This is what [3-D] Dependency Inversion looks like in practice, and it is what makes [4.4]
absolute independence achievable across a vendor upgrade.

### 3.2 Make invalid states hard to represent

Do not model something as "optional field + everyone checks it forever". Model the states that
actually exist, so the impossible combination cannot be constructed in the first place.

- Scattering optional/nullable fields pushes a presence check into every single caller — and one
  forgotten check is a crash.
- Define the precise type per state instead: a *paid* order **always** has an order ID, a payment ID,
  and a paid status; an *unpaid* order has none of them and cannot pretend to.
- Prefer a closed set of states (enum / tagged union / distinct types) over a bag of flags whose
  combinations mostly mean nothing.

If a field is genuinely optional, that must be a real business fact, not a shortcut taken because
the type was inconvenient to model.

### 3.3 Separate decisions from actions

Split the code that **decides** (business rules) from the code that **performs side effects**
(DB writes, emails, network calls, file I/O, game-state mutation).

- The deciding function takes data in and returns a decision out. It touches nothing external.
- The acting function takes that decision and carries it out. It contains no business rules.
- The decision logic is then testable on its own, with no database, no network, and no mocking.

```
// CORRECT
const decision = decideRefundEligibility(order);   // pure, returns a decision
if (decision.isEligible) issueRefund(decision);    // side effect only

// WRONG
function processRefund(order) {
    // business rules AND db writes AND email sending, all tangled
}
```

Related to but stronger than [6.2] CQS: CQS governs a single function, this governs the split
between whole modules. `T1_` files state where that boundary sits on their stack.



---

## 4. FILE STRUCTURE & MANAGEMENT

### 4.1 File header — path + purpose

Each source-code file starts with a comment containing its real path relative to the
project root and a one-line responsibility. Use the language's comment syntax, defined
in T1. Prefer an actual slash-separated path so it matches the file on disk.
Formats that do not permit comments, generated files, and required first-line directives
(such as a shebang) retain their required format; place the header at the first legal
position or document the responsibility outside the file.

### 4.2 File naming

Names describe responsibility and must be valid for the language's import mechanism
and the framework's discovery/serialization rules. Concrete casing, extensions, role
suffixes, folder conventions, and class/file matching belong in the active T1.
Never require folder names to be duplicated as dots in on-disk filenames.

### 4.3 Single responsibility per file

Each file does ONE job only.

- Do not mix unrelated logic in the same file.
- Only functions that directly serve the purpose stated in [4.1] belong here. A function that does
  not serve that purpose gets **moved to the correct file**, not left behind.
- Two functions must never overlap in responsibility.

### 4.4 Absolute independence — top priority

A change in File A must never break File B.
The internal structure of other files stays intact and untouched.



---

## 5. LANGUAGE & NAMING CONVENTIONS

| Entity | Universal requirement |
|---|---|
| Class/type | Meaningful English domain noun; casing belongs in T1. |
| Function/method | Meaningful English action or query; framework-fixed names remain exact. |
| Variable/member | Descriptive English business meaning; casing and visibility prefixes belong in T1. |
| Logs/comments | Vietnamese without diacritics by default; a T1/T2 may explicitly override. |
| UI/user-facing messages | English by default; target audience overrides belong in T2. |

### 5.1 Logs & comments

```
[INFO]    Khoi tao module thanh cong
[WARN]    Ket noi cham, thu lai
[ERROR]   Khong tim thay file cau hinh
[DEBUG]   Gia tri bien: ...
[SUCCESS] Luu du lieu thanh cong

// Day la ly do tai sao xu ly theo cach nay
```

Only these 5 prefixes are valid: `[INFO]` `[WARN]` `[ERROR]` `[DEBUG]` `[SUCCESS]`.

### 5.2 User-facing text

English by default — this covers all frontend labels/buttons/messages and all backend messages
shown to users. If a project targets a different audience/language, that project's `T2_` may
override this rule; with no override, the default is English.

### 5.3 Name by meaning, not by shape

A name must state the **business concept**, not the container holding it. Generic placeholder
names force every future reader to go re-derive what the value actually is.

| Banned | Use instead |
|---|---|
| `data`, `result`, `item`, `value`, `obj`, `info` | `pendingOrder`, `paidInvoice`, `expiredSession` |
| `list`, `arr`, `temp`, `stuff`, `misc` | `unshippedOrders`, `bannedPlayerIds` |
| `handler`, `manager`, `helper`, `utils`, `common` | name the actual job: `orderValidator`, `priceCalculator` |

This applies to variables, functions, classes, and file names alike. If no specific name can be
found, that is the signal the unit is doing several things at once — split it (SRP, [3-S]).

### 5.4 Comment purpose

Comments explain **"WHY"**, never **"WHAT"**.

```
// WRONG — restates what the code already says
// Tang toc do len 1.5 lan
currentSpeed = currentSpeed * 1.5;

// CORRECT — states the business reasoning
// Bat buoc nhan 1.5 vi khach hang VIP duoc uu dai dac biet khung gio vang
if (isVip && isGoldenHour) {
    currentSpeed = currentSpeed * 1.5;
}
```

If function and variable names are already clear, **no extra comment is needed**.



---

## 6. ADDITIONAL CLEAN CODE STANDARDS

> Guiding principle for this entire section: **make the next change easier.**
> Good code is not more clever code — it is code that is easy to understand, easy to change,
> and reliable enough that someone else can maintain it long after it was written.

- **KISS** — keep code simple and explicit. Avoid one-liners or shorthand tricks that hurt readability.
- **DRY** — do not repeat the same logic more than twice. On the third occurrence, extract it into a shared function/module immediately.
- **PARAM** — each function takes **at most 2 parameters**. If more are needed, group them into a single config Object/Class.
- **FAIL-FAST / GUARD CLAUSE** — validate inputs at the VERY START of the function, return/throw early on invalid data, avoid deeply nested if-else chains.

```
// CORRECT
function processOrder(order) {
    if (!order) return;
    if (!order.items.length) return;
    // ... main logic
}

// WRONG
function processOrder(order) {
    if (order) {
        if (order.items.length) {
            // ... main logic, deeply nested
        }
    }
}
```

### 6.1 Quantitative thresholds

| Metric | Threshold |
|---|---|
| Parameters per function | ≤ 2 (more → group into a config object) |
| Function length | ≤ 30 lines, doing exactly one thing |
| Cyclomatic complexity | < 10 |
| Nesting depth | ≤ 3 levels |

Exceed a threshold in code you are writing or changing → **split it** into smaller functions on
your own; no need to ask. If it cannot be split any further, leave it as it is — no reason needs to
be recorded.

Required framework callbacks keep their exact signature, including parameter count.
T1 lists the affected callbacks; internal hand-written functions still obey the limits.

### 6.2 Additional function rules

- **YAGNI** — do not implement features nobody has asked for yet.
- **Magic values** — never hardcode numbers/strings in business logic; declare clearly named constants.
- **Law of Demeter** — avoid deep call chains (`a.b().c().d()`); pull out a named intermediate variable.
- **CQS** — a function either changes state or returns data, never both.
- **Immutability** — never mutate data structures returned directly by an external API/library; make a safe copy first.
- **Idempotency** — initialisers and event registrations must be safe to call repeatedly: no leaks, no duplicated logic.
- **No accidental globals** — keep state encapsulated. A runtime-required public namespace must be defined and constrained in T1; project-specific prefixes belong in T2.

### 6.3 Error handling

- An error is **either** handled **or** propagated upward — never swallowed silently.
- No empty `catch`. At minimum, log it with the `[ERROR]` prefix plus context.
- Do not use exceptions for normal control flow ("not found" is a return value, not an error).
- An error message must say **what** went wrong and **where**, not just "failed".
- **Predictable error codes.** Expected failures carry a stable, enumerated code (`ORDER_NOT_FOUND`,
  `INSUFFICIENT_FUNDS`) so callers can branch on it consistently. Never make a caller parse a
  human-readable message to decide what happened.
- **Context in the log, not in the user's face.** The log line carries what the developer needs
  (identifiers, the operation, the failing input); the user gets the stable code plus a plain message.
- **Never log secrets.** Passwords, tokens, API keys, session IDs, full payment details, and personal
  data must never reach a log, an error message, or a stack trace. Redact at the point of logging,
  not afterwards.



---

## 7. CRUD STANDARDS

### 7.1 Data layer separation

Separate persistence and external I/O from presentation and business decisions.
T1 defines the concrete layers/adapters for its context; do not mandate a framework-specific
Repository/Service/Model layout for every project. UI/controllers call an appropriate boundary.

### 7.2 CRUD naming intent

| Operation | Prefix | Example |
|---|---|---|
| CREATE | `create…` `add…` `insert…` | `createUser()`, `addOrder()`, `insertRecord()` |
| READ | `get…` `find…` `search…` | `getUserById()`, `findActiveProducts()`, `searchByKeyword()` |
| UPDATE | `update…` `modify…` | `updateProfile()`, `modifyStatus()` |
| DELETE | `delete…` `remove…` | `deleteAccount()`, `removeItemFromCart()` |

### 7.3 Delete integrity

Identifier casing and exact spelling follow T1; the examples illustrate intent only.

Before implementing Delete, the choice between these two belongs to the user:
- **Hard Delete** — physically remove the record from the system.
- **Soft Delete** — hide or flag the record (`isActive = false`); data is retained.

If the request or `T2_` already says which one, follow it. Otherwise **ask** ([0.8], section 1.2) —
do not choose on the user's behalf.



---

## 8. REST API DESIGN STANDARDS

Applies when designing or changing an HTTP resource API. These are stack-independent
rules; framework implementation belongs in `T1_`, and the resource contract belongs
in `T2_`. Do not add an API to a project that did not request one.

### 8.1 REST architectural constraints

| Constraint | Requirement |
|---|---|
| Client-server | Separate presentation concerns from server-side resource and business processing. |
| Stateless | Each request contains the context needed for processing; do not depend on remembered client conversational state from a prior request. Persistent resource data is still allowed. |
| Cacheable | Declare cacheability and freshness through HTTP cache controls. Prevent inappropriate caching of sensitive responses; use validators such as ETag when applicable. |
| Uniform interface | Identify resources, manipulate them through representations, use self-descriptive messages, and provide hypermedia controls for application transitions. |
| Layered system | Preserve the contract through intermediaries such as gateways, proxies, and load balancers; clients need not know every internal layer. |
| Code on demand | Optional: deliver executable client code only if explicitly required. |

For an API intended to fully conform to REST, include HATEOAS: representations expose
links or controls for relevant available transitions. Document link relations and how
clients use them. If the project intentionally omits hypermedia, document that limitation
in `T2_` rather than claiming full REST conformance. Do not invent business transitions.

### 8.2 Resource endpoints

- Use clear English plural nouns for collection endpoints: `/api/v1/users`,
  `/api/v1/products`. Identify individual resources with `/api/v1/users/{userId}`.
- Do not encode CRUD verbs in URLs: no `/getUsers` or `/createProduct`.
  This rule concerns URLs only; internal function names still follow sections 5 and 7.
- Do not use a trailing slash in the canonical endpoint: `/users`, not `/users/`.
- Keep resource names and URL structure consistent throughout the project.
- For multi-word endpoint path segments, use lowercase `kebab-case`: `abc-xys`,
  `/api/v1/order-items`, `/api/v1/payment-methods`. Do not use underscores
  (`abc_xys`, `order_items`) or camelCase in endpoint path names. This concerns
  URL path segments; JSON properties retain the API contract's `camelCase`; internal identifiers follow T1.

### 8.3 HTTP methods

| Method | Required semantics |
|---|---|
| GET | Read a resource or collection; do not perform business-state mutations. |
| POST | Create a resource in a collection; any other processing semantics must be explicitly documented. |
| PUT | Replace the target resource's representation; document whether creation at that URI is allowed. |
| PATCH | Apply a partial update using a documented patch format. |
| DELETE | Remove the resource according to the hard/soft-delete decision in section 7.3. |

GET is safe. PUT and DELETE must be idempotent: repeating the same request has the
same intended effect, although the returned status may differ. POST and PATCH are
not automatically idempotent; do not retry them blindly.

### 8.4 HTTP status codes and errors

Never return `200` for every outcome or disguise a failure as a successful response.

| Code | Use |
|---|---|
| 200 OK | Successful request with a response body, commonly GET, PUT, or PATCH. |
| 201 Created | A resource was created; identify it in the response and provide `Location` when appropriate. |
| 204 No Content | Successful request with no response body, commonly DELETE or an update. Never attach a JSON body. |
| 400 Bad Request | Malformed request or invalid request syntax/structure. |
| 401 Unauthorized | Missing or invalid authentication; include the applicable `WWW-Authenticate` challenge. |
| 403 Forbidden | Access is refused, such as insufficient permission. |
| 404 Not Found | The requested resource does not exist or is not disclosed. |
| 422 Unprocessable Content | Understood content type and valid syntax, but the supplied instructions or field values cannot be processed. |
| 429 Too Many Requests | Request limit exceeded; document retry behavior and send `Retry-After` when available. |
| 500 Internal Server Error | Unexpected server failure; do not expose internal details. |

These are common codes, not an exhaustive whitelist. Use other standard codes when
their semantics apply. Keep the distinction between 400 and 422 consistent and documented.
Error responses follow section 6.3: stable machine-readable code plus a plain English
message; diagnostic context stays in redacted logs. Keep one documented error schema.

### 8.5 API versioning and compatibility

- Establish a versioning strategy from the beginning: URL version such as
  `/api/v1/users`, or a documented header/media-type strategy.
- Use one strategy consistently; record the project's chosen strategy in `T2_`.
  If no strategy is established, ask before implementing competing alternatives.
- Preserve existing client contracts. Breaking changes require an explicitly approved
  migration/version plan; do not silently change a published contract.
- Adding versioned routes is not permission to bump project or API versions. Section 2.6
  still applies; version changes require the user's request.

### 8.6 Representation and JSON contract

- JSON is the default for structured request and response bodies. Use the correct
  `Content-Type` and respect supported response formats indicated by `Accept`.
- JSON property names use `camelCase`, such as `firstName` and `createdAt`, unless
  `T2_` explicitly overrides this. `first_name` is snake_case, not camelCase.
- Keep field types, nullability, response schemas, and error schemas consistent and documented.
- JSON is not required for bodyless responses or file/binary transfers. Support XML or
  other representations only when the project requires them; do not add unused formats.

### 8.7 Pagination, filtering, and sorting

- Do not return an unbounded large collection. Provide pagination with a documented
  default and maximum page size; validate client-supplied limits.
- Use query parameters for collection controls. Examples:
  `?page=2&limit=20`, `?offset=20&limit=20`, `?sort=createdAt:desc`, `?status=active`.
- Choose one documented pagination contract for each collection. Do not silently mix
  page, offset, or cursor conventions.
- Use deterministic ordering and document supported filter/sort fields and pagination
  metadata or navigation links. Validate and allowlist query fields before data access.

### 8.8 Authentication, authorization, and transport

- Require HTTPS for deployed APIs. Local development exceptions belong in `T1_`/`T2_`.
- Protect non-public resources with an established authentication mechanism and enforce
  authorization for each operation and resource. Client-side checks are insufficient.
- OAuth 2.0 is an authorization framework; JWT is a token format, not a complete
  authentication mechanism. Do not treat them as interchangeable solutions.
- Validate tokens using the selected mechanism's rules, including signature, expiry,
  issuer, and audience where applicable. Follow section 6.3 for secret redaction.
- Apply documented rate limits and return 429 when exceeded. Rate limiting reduces
  abuse; it is not a complete DDoS defense.
- Record the authentication mechanism, public endpoints, permissions, and limits in
  `T2_`; ask if a necessary security decision has not been specified.

### 8.9 API documentation and validation

- Maintain a clear API contract using OpenAPI/Swagger, Postman documentation, or an
  equivalent agreed format. Do not introduce a framework-specific tool into core.
- Document authentication, endpoint/method pairs, path/query parameters, request and
  response schemas, status/error codes, examples, pagination, rate limits, caching,
  versioning, and compatibility expectations.
- Include request/code examples without real credentials or personal data.
- Validate changed endpoints using Given/When/Then (section 9.1): success, invalid
  input, and an edge case. Where applicable, also verify unauthorized/forbidden access,
  missing resources, pagination bounds, rate limits, idempotency, and bodyless 204 responses.

### 8.10 Normative references

- HTTP semantics and status codes: [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html).
- PATCH: [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html).
- HTTP caching: [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html).
- Rate-limit status 429: [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html).
- OAuth 2.0: [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html).
- JWT: [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html).
- REST constraints: [Fielding, chapter 5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm).

---

## 9. VALIDATION & TESTING

### 9.1 Testing — Given / When / Then

- **Given**: the starting state
- **When**: the action performed
- **Then**: the observable result

Every new feature needs at minimum: one success case, one invalid-input case, one edge case.

### 9.2 Validation checklist

- [ ] Read this entire file
- [ ] Checked whether `T1_` / `T2_` are present; emitted the 0.3 warning if not
- [ ] Checked whether the project defines any overrides, and wrote an `Override:` line for each
- [ ] Header carries the real relative path and purpose, at the first legal location ([4.1])
- [ ] File naming is valid for the language/framework and follows T1 ([4.2])
- [ ] File contains only functions serving its stated purpose ([4.3])
- [ ] Identifier casing and filenames follow the active T1; names are meaningful English
- [ ] Logs & comments → Vietnamese, **no diacritics**, one of the 5 valid prefixes
- [ ] UI text & user-facing messages → English
- [ ] Comments explain WHY, not WHAT
- [ ] SOLID principles applied correctly
- [ ] CRUD functions follow the naming convention; data layer is separated
- [ ] Each function has ≤ 2 parameters (or a grouped config object)
- [ ] Each function ≤ 30 lines, complexity < 10, nesting ≤ 3 levels
- [ ] Guard clauses used instead of nested if-else
- [ ] Names state the business concept; no `data` / `result` / `item` / `manager` placeholders ([5.3])
- [ ] External systems are translated at a single boundary; no vendor shapes leaking inward ([3.1])
- [ ] States are modelled precisely; no bag of optional fields every caller must re-check ([3.2])
- [ ] Decision logic is separated from side effects and testable on its own ([3.3])
- [ ] Expected failures carry a stable error code; no secrets in any log or message ([6.3])
- [ ] The change set has ONE stated purpose and can be rolled back on its own ([2.5])
- [ ] Commit message follows Conventional Commits: English type/scope, Vietnamese no-diacritics description ([11.2])
- [ ] Commit description is imperative, lowercase, ≤ 72 chars, no trailing period ([11.2.3])
- [ ] Breaking change carries both `!` in the header and a `BREAKING CHANGE:` footer ([11.2.6])
- [ ] Did not commit anything the user did not explicitly ask to commit ([11.2.8])
- [ ] No magic numbers/strings in business logic
- [ ] No empty catch; every error is logged or propagated
- [ ] No logic repeated more than twice
- [ ] No leaks into global scope
- [ ] No features added outside the requested scope
- [ ] No unrequested edits to surrounding files, no refactor without permission
- [ ] Anything ambiguous was asked, not decided; nothing was implemented on a guess ([0.8], [1.2])
- [ ] Version numbers untouched
- [ ] REST APIs follow section 8: resource URLs, HTTP semantics, status codes, versioning, JSON contract, pagination, security, caching, and documentation



---

## 10. DEBUGGING & MAINTENANCE MINDSET

- **Rubber Duck Debugging** — for hard bugs, systematically comment out blocks and log key values to trace the flow.
- **Premature Optimization Guard** — write correct, stable architecture first. Only optimize when there is **measurable evidence**.
- **10x Rule** — code is read far more often than it is written. Prefer clear layout, sensible whitespace, and expressive naming over saving a few lines.



---

## 11. DELIVERY & GIT COMMITS

### 11.1 Mandatory response format

```markdown
## Solution: [Feature Name]
### Analysis
### File Structure
### Code
#### File: [relative/path/to/file]
### Testing Guide
### Notes & Maintenance
### Changelog
```

`Notes & Maintenance` must list every `Override:` line (0.6) and every piece of code commented out as dead code ([2.4]).

### 11.2 Commit message convention

Conventional Commits. The **structure and keywords are English**; the **description, body, and
footer text are Vietnamese without diacritics** — the same rule as logs in [5.1], for the same
reason: git tooling, terminals, and CI output are not reliably UTF-8 safe.

```
<type>(<optional scope>): <mo ta ngan, tieng Viet khong dau>

[than bai, tieng Viet khong dau]

[footer]
```

#### 11.2.1 Type — required

| Type | Use for |
|---|---|
| `feat` | adds an entirely new feature |
| `fix` | solves a bug or unexpected error |
| `docs` | documentation only (README, this ruleset, `T1_`/`T2_` files) |
| `style` | formatting only — whitespace, semicolons; no logic change |
| `refactor` | rewrite without changing external behaviour and without fixing a bug |
| `perf` | a rewrite specifically to improve performance |
| `test` | new automated tests, or updates to existing suites |
| `build` | build tooling, internal scripts, dependencies |
| `ci` | pipelines, workflows, infrastructure definitions |
| `chore` | maintenance that touches no code logic |

One commit = one type. If two types apply, that is two commits ([2.5]).

#### 11.2.2 Scope — optional

A noun naming *where* the change lives, in parentheses: `feat(economy):`, `fix(playerHUD):`.
Use the module/cog/system name, not a file path. Omit it rather than inventing a vague one.

#### 11.2.3 Description — required

- **Vietnamese, no diacritics**, imperative present tense: `them`, `sua`, `xoa`, `doi` —
  never `da them`, `dang sua`, or a past-tense form.
- Target **≤ 50 characters**; **never exceed 72**.
- Start lowercase. **No trailing period.**

#### 11.2.4 Body — optional

Explains **why** the change was made and what motivated it — not what the diff already shows
(same principle as section 5.4). Vietnamese, no diacritics, wrapped at ~72 characters.
Separated from the header by **one completely blank line**.

#### 11.2.5 Footer — optional

- Issue references: `Closes #123`, `Refs #456`
- Breaking changes: see 11.2.6
- Separated from the body by **one completely blank line**.

#### 11.2.6 Breaking changes

If the change breaks existing behaviour, **both** of these are required:

1. A `!` immediately before the colon in the header: `refactor(api)!: ...`
2. A `BREAKING CHANGE:` block in the footer explaining what breaks and what to migrate to.

#### 11.2.7 Examples

```
feat(economy): them lenh chuyen tien giua nguoi choi

Nguoi choi co the chuyen FoxCoin cho nhau qua lenh /transfer.
Gioi han 3 lan moi ngay de tranh lam dung trong server dong nguoi.
Moi giao dich do server quyet dinh, client chi gui yeu cau.

Closes #142
```

```
fix(playerHUD): sua loi HUD bien mat khi doi nhan vat

Su kien OnCreatePlayer duoc dang ky lai moi lan doi nhan vat nen
handler cu khong bi go, gay ve chong len nhau roi mat HUD.

Refs #98
```

```
refactor(api)!: doi ten truong balance thanh coinBalance

BREAKING CHANGE: client cu doc truong `balance` se khong con hoat
dong. Can cap nhat sang `coinBalance` truoc khi deploy ban moi.
```

| Wrong | Why |
|---|---|
| `Fix bug.` | no type, capitalised, trailing period, says nothing |
| `feat: Them tinh nang moi` | capitalised description, and "tinh nang moi" carries no information |
| `feat(economy): đã thêm lệnh chuyển tiền` | has diacritics, and past tense instead of imperative |
| `feat: them lenh transfer va sua loi HUD va update README` | three types in one commit — split it ([2.5]) |

#### 11.2.8 Agent behaviour

- **Never commit unless the user explicitly asks.** Producing code is not permission to commit it.
- When asked to commit, propose the message first if the change touches more than one file.
- Never `--amend` an existing commit or force-push unless explicitly told to.
- The commit type must match what actually changed. Do not label a behaviour change as `refactor`,
  and do not hide a fix inside a `chore`.
<!-- End of project agent rules. -->
