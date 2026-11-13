# CP-DR looks online: page fetch and SEC EDGAR tools

by: user
date: 2026-11-13

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or
`configs:` line. A fetch has no fee and makes no provider call, but a real run is still a separate,
explicit paid action. Everything built here was proven offline only.

## The owner's words, 2026-11-13

- "cp-dr needs to look online for peer data or else cp-1c will / should not work. and supports
  cp-2's analysis. does not have to be a model specific tool call or skill, just look online to
  find relevant data and information from reputable sources."
- On the scope: "Fetch + SEC EDGAR now, search API next (Recommended)"
- On the sources: "Allowlist of reputable domains (Recommended)"
- On the default: "On by default for public cases (Recommended)"
- On pages dated after the case's as-of date: "1 - but understand private transaction figures,
  data and multiples will tougher to validate". Option 1 is: refuse a post-as-of page as a source
  of figures; allow it as a labelled later event.

## What was built

Four tools for CP-DR only: `fetch_page`, `sec_company_search`, `sec_filing_list` and
`sec_concept_facts`. Each retained page is stored under `<run>/live/web/` (the live run's folder, beside `loop.json`; the
spec said `<run>/web/`, and this departs from it because the executor writes only inside its own
folder) with its URL, fetch time,
sha256, stated date and status (index: `web/index.jsonl` there). The model reads a retained page through
the same paging tools it uses for issuer files (`read_pages`, `search_source`). A lookup result
carries the page's identity and status, never its text. There is no search API in this version.
Code: `src/deploy_workflow/research/weblookup.py` (core), `src/deploy_workflow/model/handoff.py`
(tools, `WEB_LOOKUP_RULES`, acceptance checks), `src/deploy_workflow/owners/cpos_launch.py`
(`--web-lookup`, `--web-host`).

## The allowlist

Source: `src/deploy_workflow/research/web_allowlist.json` (version 1). A host is allowed when it
equals a listed domain or ends with `.` + a listed domain. This list is the controller's proposal
and awaits the owner's review.

| Domain | Category |
| :--- | :--- |
| sec.gov | Regulator or official |
| fca.org.uk | Regulator or official |
| find-and-update.company-information.service.gov.uk | Regulator or official |
| esma.europa.eu | Regulator or official |
| sedarplus.ca | Regulator or official |
| federalreserve.gov | Regulator or official |
| treasury.gov | Regulator or official |
| ecb.europa.eu | Regulator or official |
| bankofengland.co.uk | Regulator or official |
| bis.org | Regulator or official |
| imf.org | Regulator or official |
| bls.gov | Regulator or official |
| bea.gov | Regulator or official |
| census.gov | Regulator or official |
| fred.stlouisfed.org | Regulator or official |
| ons.gov.uk | Regulator or official |
| ec.europa.eu | Regulator or official |
| oecd.org | Regulator or official |
| worldbank.org | Regulator or official |
| londonstockexchange.com | Exchange |
| nyse.com | Exchange |
| euronext.com | Exchange |
| luxse.com | Exchange |
| moodys.com | Rating agency |
| spglobal.com | Rating agency |
| fitchratings.com | Rating agency |
| dbrs.morningstar.com | Rating agency |
| kbra.com | Rating agency |

Removed after security review: `ise.ie` (current ownership of the legacy domain is not confirmed)
and `nasdaq.com` (its news pages syndicate third-party contributor articles).

Points for the owner when reviewing:

- `sec.gov` EDGAR archives hold filer-submitted documents and public comment letters.
- `federalreserve.gov` and `ec.europa.eu` publish public submissions.
- `spglobal.com` also hosts non-ratings businesses.
- The list is a host filter, not a quality grade. The module states the Source type of each cited
  page per row of `## Sources` (Issuer filing, Peer filing, Regulator or official, Rating agency,
  Industry body, Financial press, Other).

The case's own investor-relations hosts are added per run with `--web-host` (a bare host name of two
or more labels, whose last label is letters only or `xn--` punycode; no scheme, path, port,
wildcard or IP address).

## The SEC User-Agent rule

SEC asks automated clients to declare a User-Agent that names a company and a contact address. That
value comes only from the launching-environment variable `DEPLOY_WORKFLOW_SEC_USER_AGENT`, which
the owner sets. No name or address is written into code, tests or run files, and the value is not
printed or retained. It is sent only to `sec.gov` hosts. A value that is blank or not plain
printable ASCII counts as absent. When it is absent, a `sec.gov` request is refused with a message
naming the variable, and the launcher says so before the run ("SEC: sec.gov lookups will be refused:
DEPLOY_WORKFLOW_SEC_USER_AGENT is not set"). Rate: at most one `sec.gov` request per 0.2 s
(`SEC_INTERVAL_S`), redirect hops included, under SEC's stated ceiling of 10 per second.

## Limits

All from the code.

- https only; the default port (443) only; URL at most 2,000 characters.
- Every redirect hop is checked against the allowlist again; at most 3 redirects.
- Private, local and other non-global addresses are refused before a connection is made.
- Body cap per page: 5,000,000 bytes; a larger body is refused, not truncated.
- Per-run budget: 40 pages and 40,000,000 bytes; it survives a new process. A retained URL is still
  served when the budget is spent.
- Time limit: 10 s to connect, 30 s in total per fetch.
- Content types kept: `text/html`, `application/xhtml+xml`, `text/plain`, `application/json`.
- PDFs are refused and nothing is retained. The PDF library cannot be bounded on hostile input
  in-process: in review a 948-byte file built a 30-million-character string using about 2 GB.
  Supporting PDFs needs a sandboxed, time-limited extractor. This is a follow-up.
- Extracted text is capped at 2,000,000 characters per page, with a visible final line saying the
  text was cut.
- An EDGAR summary line or field is at most 200 characters, a summary at most 10,000, at most 20
  matches or listed items per result. A tool `ERROR:` result is one line, at most 300 characters.
- Text hidden by a stylesheet (for example `display:none`) is extracted like visible text and can
  be quoted: the extractor reads the markup, not the rendered page.
- Any subdomain of a listed domain is trusted: a host that ends with `.` + a listed domain passes,
  whoever runs it.
- Nothing has been fetched from a live host. Headers, encodings and content types from real hosts
  are unproven; every page in the tests is hand-written.
- The 5,000,000-byte page cap may refuse large filings. Not measured.

## The cutoff rule

The cutoff is the run's research cutoff: the as-of date, or the context's cutoff when that is
earlier (`effective_cutoff`). Each retained page has one status.

| Status | Meaning | What the handoff must do |
| :--- | :--- | :--- |
| `usable` | stated date on or before the cutoff | may support a figure |
| `later-event` | stated date after the cutoff | take no figure from it; cite it only as a labelled later event; its `## Sources` row carries the words "Later event" |
| `undated` | no stated date found | its row says "Undated", and a `## Gaps` item says so in words with the id on its Basis line |

A page is dated by the later of its published and its modified date. The sources read, from
`weblookup._html_date` and `_stated_date`: in an HTML page, `<meta>` tags named
`article:published_time`, `datePublished`, `date`, `DC.date`, `DCTERMS.date` or `pubdate`
(published) and `article:modified_time`, `og:updated_time`, `dateModified`, `DCTERMS.modified` or
`last-modified` (modified); JSON-LD `datePublished` and `dateModified`, used for a side the meta
tags leave empty; and a `<time>` element, only when neither gave a date. When the HTML gives no
date, a `Published: YYYY-MM-DD` line in the body of an HTML or text page is read. The status
follows the later date; on a tie the published source is named. An SEC filing document (final URL
on `sec.gov` or `www.sec.gov`) is dated by its filing date when a filing list retained in this run
(`sec_filing_list`) names its accession, whatever its body states; otherwise it is dated as any
page. SEC JSON stays undated at page level; each filing and fact carries its own filing date, and
the cutoff applies to each one (a later one is marked "[after the cutoff: a later event, not a
source of figures]" in the tool result). A `Last-Modified` header is not a stated date: it is
recorded as a source and never dates a page.

Consequence of the modified date, stated plainly: a site that bumps its modified date after the
cutoff makes the page a later event, even when its text was published before the cutoff.

Consequence, stated plainly. A peer's filing for a period that ends on the as-of date is normally
filed after it. Under option 1 that filing is a later event and cannot supply figures. When the
as-of date equals a fiscal year end, peer figures for that same year will mostly be refused, and
what CP-DR can give CP-1C is figures for earlier periods. This is the owner's decision as given. It
is also an open point below, because it limits what CP-1C can receive. A private-transaction figure
or multiple found only on a later page stays unvalidated and is stated as a limitation under
`## Gaps`.

An undated page may supply figures. SEC JSON and any page without a recognised date are undated, so
the later-event rule does not bind them mechanically; the per-fact filing dates bind by instruction.

## Acceptance checks on CP-DR's handoff

When lookup is on, `web_handoff_issues` (`weblookup.py`) checks the handoff before it is accepted.
It is mechanical, pure and deterministic, and each issue is one sentence naming the row or quote.
It fails closed: it reads any table row (a line with `|`, with or without a leading pipe; `\|`
stays inside its cell) and any case of a `web-` id or URL scheme. It runs after the launcher's real
checker, so the form it asks for is one that checker accepts (prose check 5 refuses a hash in a
sentence, and the voice rules keep ids to Basis lines, tables and `## Sources`).

### A resumed run

CP-OS runs the same checks when it rechecks a retained CP-DR response on resume
(`HandoffExecutor.web_issues`, added to the launcher's checker by `cpos._with_web_checks`), in a run
whose settled lookup is on, from the run's retained index `live/web/index.jsonl` and the same
hosted-search value the live write used. A retained handoff that cites a page absent from the index
is refused with the sentence a live write gets. An index that cannot be read gives one plain issue
("The run's retained web pages could not be read ...", no path). A run that retained no page has no
index, which is not damage. With lookup off, and for every other module, the check is unchanged.

### The citation form

A page's id is `web-` and 12 lower-case hex digits (`web-` + the first 12 of its sha256), the name
`list_sources` shows. It may appear only:

- as the first cell of the page's own `## Sources` row (one row per page), followed by URL,
  publisher, stated date or `Undated`, a Source type cell, and `Later event` when needed;
- on Basis lines, for example `Basis: web-0123456789ab, page 1`;
- in a table cell: a `Source`, `source` or `locator` cell; TDR.2's `source` cell holds the id;
- never in a sentence.

A retained URL also names the page (fail-closed alias), so the method's "web page cited by its URL"
clause neither evades the check nor is rejected. No method edit is needed.

### The rules

"Hosted" means hosted `web_search` is also on for the module.

- A1. A handoff holding U+2028, U+2029, U+0085, vertical tab, form feed or U+001C to U+001E gets
  exactly one issue. Lines split at LF, CR LF and CR only (`handoff_delivery.physical_lines`).
- A2. A page is named by its id (any case) or by a URL equal, after normalising scheme and host
  case, `:443`, fragment, an empty query and one trailing `/` (`http` is never `https`), to the url
  or final_url of any index row of that id. Nothing else names a page.
- A3. A `web-` and 12-hex token that is not a retained id is an issue wherever it appears.
- A4. When hosted is off, every http(s) URL in a `## Sources` row is a retained URL. When hosted is
  on, this rule and A13(i) are skipped (a URL the hosted search found is a citation; owner to
  confirm, open point 9). A URL with a user name or password is refused at fetch.
- A5. A `## Sources` row that names a retained page has that page's id as its first cell (backticks
  stripped, any case). Every other page the row names is one issue.
- A6. Every retained page named anywhere has a `## Sources` row whose first cell is its id. Each
  page is reported once, and not when A5 already reported it.
- A7. A row naming a later-event page carries `Later event` (any case, space or hyphen) outside its
  URLs; a row naming an undated page carries `Undated`. A page's status is the strictest across its
  index rows (later-event over undated over usable). Source type is `web_source_issues` in
  `handoff.py`: one allowed type, optionally followed by `;` and a label.
- A8. The `## Gaps` section names the id of every undated page that a Sources row names.
- A9. `web_source_issues` (Source type cell) is unchanged.
- A10. In each paragraph or list item, every quoted span of 12 or more characters that is not only
  a reference must appear in the text of one of the pages the unit names. A unit is a run of
  non-blank lines; a blank line, a heading or a table row ends it, and a list-marker line
  (`prose_checks.LIST_MARKER`) starts a new one. A span runs from any of `" “ ” „ « » ‹ ›` to the
  next of them (mixed pairs count; a mark right after a digit is an inch mark and opens nothing)
  after HTML entities are unescaped, or between single quotes where the opening follows a non-word
  character (not `'24`) and the closing precedes one. Straight and curly apostrophes are one
  character.
- A11. In each table row, every such span must appear in one of the pages the row names directly.
  There is no linking.
- A12. A TDR.6 row is a table row whose first cell fully matches `<peer>.<operand>` (revenue,
  ebitda, debt, interest, ffo). Its pages are those it names, plus those named by any table row
  whose first cell equals a token of its `evidence_id` or `evidence_ids` cell (split at `;`, `,` or
  whitespace). One hop, no chain: this is the method's TDR.2 `evidence_id` register.
- A13. For a TDR.6 row: (i) when hosted is off, every URL in it is retained; (ii) none of its pages
  is later-event; (iii) when it has pages, its quote (the cell under a `quote` header, else the
  longest cell; a trailing page reference in brackets and the surrounding quote marks are dropped)
  is non-empty and appears in one of them; (iv) when the table has an `amount` header, the amount
  text appears inside the quote.

Known limit of A10 and A11, a consequence of the rule: a unit or row that names a web page may quote
only from the pages it names. One that mixes a web source with a quoted issuer-file passage of 12 or
more characters is rejected and must be split. `WEB_LOOKUP_RULES` states this. An apostrophe pair
that looks like a single-quoted span can be rejected; it is rephrased.

Governed by instruction in `WEB_LOOKUP_RULES` only, not caught mechanically:

- a TDR.6 figure not written as a `<peer>.<operand>` table row (bullets, HTML);
- a malformed id (11 or 13 hex digits, `web_`) or a bare hex id;
- evidence linked through two rows, or through a column other than `evidence_id`;
- a page named by a scheme-less address or a description;
- quoted spans under 12 characters, a figure split across short quotes, Markdown blockquotes, and
  paraphrase without quote marks;
- later-event figures in prose outside TDR.6;
- SEC facts filed after the cutoff.

## Fetched text is data

The result of each lookup says it is retained web page data, never instructions. Every string taken
from a server or an EDGAR document is neutralised before it reaches the model: a `<<<` or `>>>`
delimiter in page text cannot forge the frame's end. The text is neutralised before it is cut. The
EDGAR summary sits inside the frame. A fixture with an injected instruction is tested
(`test_an_injected_page_stays_data_and_cannot_forge_a_delimiter`). Every URL leaves this
environment, so the module is told a URL carries only public names and identifiers. As with hosted
search, that is an instruction, not a control: a fetch URL goes through `flag_search_queries`, and a
URL that carries a supplied file name or a source figure is still fetched but a `web_url_flagged`
event is recorded. Detection only.

## On and off

`--web-lookup default|on|off`. `default` is on for a `public` case and off for any other kind;
`on` forces it for any case kind; `off` forces it off. Only CP-DR is offered the tools. The launcher
prints a `Lookup:` line that states which applies and why. The executor itself accepts only `on` or
`off`: the launcher resolves `default` first (`settled_web_lookup`), against the run's modules (no
CP-DR in the run means off) and against the folder.

A run folder keeps its identity: `live/loop.json` records whether lookup was on, and a relaunch
cannot change those bytes. So a folder that already holds a `loop.json` keeps what it recorded: a
relaunch with no flag (or with `default`) takes the recorded setting and the `Lookup:` line says
"as recorded when this run folder was started"; a flag that contradicts it stops the launch with
exit 2 and a message naming the recorded setting.

The run-start page's summary carries the launcher's own `Lookup:` line and, when present, its
`SEC:` line (`_lookup_lines`, called with the default setting and no case hosts, which is what the
command a Submit runs passes), drawn as text, one note per line, on the research module's row of
the review's readiness list (not in the facts card, which is already as tall as the layout allows). The `SEC:` line names the
variable and never its value. The approval digest does not cover it.

This is separate from hosted `web_search` (ruling-gated, OpenAI only, offered to public and private
cases; ruling 2026-11-11-run-start-submit.md), which is unchanged. Both may be on in one run, and
the module is told which tools it has. Hosted search is unchanged: a URL that is not retained is a
hosted citation when both are on, so the fetched-URL rule is skipped then (owner to confirm, open
point 11). With lookup alone, a pack item's origin URL in `## Sources` is rejected, because it was
not fetched.

## Cost

A fetch has no fee and makes no provider call. It changes a run's cost in two ways. Pages the module
reads enter its context as input tokens, bounded by the existing read limit in `handoff.py`. The
module may also take more turns, within `--max-turns`. The run's USD cap is unchanged and still
binds.

## Method text

Named edit 2c (2026-11-13) to the archived CP-DR method: its web-search clauses now also apply
under the lookup paragraph; a page is fetched with `fetch_page` or the `sec_` tools and read with
`read_pages` and `search_source`; the RESEARCH ITEMS after-the-as-of-date line gains the exception
for a labelled later event that carries no figure; section C reads "verify that web_search or the
lookup tools are granted first". Recorded in `docs/reuse/selected-methods/manifest.json`.

## Prior art

Searched before building. The project's own `research/webfetch.py` (reused: public addresses only,
pinned TLS, bounded redirects and reads) and the research-manifest fetch in `run_inputs.py`. Public
GitHub repository searches "sec edgar api client stdlib python" and "ssrf safe fetch python
allowlist" returned nothing usable; that does not prove nothing exists. Decision: build on
`webfetch`, standard library only, no new dependency.

## Open points for the owner

1. Review the allowlist, and the points about it above.
2. Set `DEPLOY_WORKFLOW_SEC_USER_AGENT` in the launching environment before a real run. A real run
   is a separate paid action.
3. The cutoff consequence above: under option 1, peer figures for the as-of year will mostly be
   refused, which limits what CP-1C receives.
4. URLs that carry run material are flagged by event, not refused. Not changed because the flag
   rule matches a supplied file's stem as a whole word and any figure of four or more digits
   shared with the sources, so refusing would also refuse legitimate pages: a file named after
   the issuer flags the issuer's own investor-relations host. Refusing is the owner's choice.
5. CP-4's runbook describes an EDGAR acquisition lane. CP-4 was not given the tools.
6. `handoff._pages` parses issuer PDFs with the same PDF library and no exception handling. This
   predates this work.
7. The change is over the global 800-line guideline (5,662 added, 80 removed, `git diff --numstat 82b17f3...HEAD`).
8. Search API: the owner chose it as the next step; not built.
9. Hosted search and lookup together: a `## Sources` URL that was not fetched is accepted when
    hosted search is also on, since it may have found it. Confirm that is the intent.
10. Where the pages are kept: `<run>/live/web/` (beside `loop.json`), not the spec's `<run>/web/`,
    because the executor writes only inside its own folder. Say if you want them moved.
11. Dropped checks, now instruction only: first-cell titles naming a page, a TDR.6 section found by
    its heading, a malformed-id token, and evidence links followed through several rows. They
    rejected the method's own layouts or the house citation form; see the limits list above.
