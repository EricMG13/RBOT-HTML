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
`sec_concept_facts`. Each retained page is stored under `<run>/web/` with its URL, fetch time,
sha256, stated date and status (index: `web/index.jsonl`). The model reads a retained page through
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

## The cutoff rule

The cutoff is the run's research cutoff: the as-of date, or the context's cutoff when that is
earlier (`effective_cutoff`). Each retained page has one status.

| Status | Meaning | What the handoff must do |
| :--- | :--- | :--- |
| `usable` | stated date on or before the cutoff | may support a figure |
| `later-event` | stated date after the cutoff | take no figure from it; cite it only as a labelled later event; its `## Sources` row carries the words "Later event" |
| `undated` | no stated date found | its row says "Undated" and `## Gaps` names its id |

A `Last-Modified` header is not a stated date: it does not make a page dated. The stated date comes
from the page's own `Published:` line or metadata. SEC JSON is undated at page level; each filing
and fact carries its own filing date, and the cutoff applies to each one (a later one is marked
"[after the cutoff: a later event, not a source of figures]" in the tool result).

Consequence, stated plainly. A peer's filing for a period that ends on the as-of date is normally
filed after it. Under option 1 that filing is a later event and cannot supply figures. When the
as-of date equals a fiscal year end, peer figures for that same year will mostly be refused, and
what CP-DR can give CP-1C is figures for earlier periods. This is the owner's decision as given. It
is also an open point below, because it limits what CP-1C can receive. A private-transaction figure
or multiple found only on a later page stays unvalidated and is stated as a limitation under
`## Gaps`.

## Acceptance checks on CP-DR's handoff

When lookup is on, `web_handoff_issues` (`weblookup.py`) checks the handoff before it is accepted.
It is mechanical, pure and deterministic, and each issue is one sentence naming the row or quote.
It fails closed: it reads any table row (a line with `|`, with or without a leading pipe; `\|`
stays inside its cell) and any case of a `web-` id or URL scheme.

Lines are read as delivery reads them: LF, CR LF and CR only (`handoff_delivery.physical_lines`).
A handoff holding U+2028, U+2029, U+0085, vertical tab, form feed or U+001C to U+001E is rejected
with one issue asking to remove them.

A page is cited by its id, by a retained URL, or by the first-cell name (6 or more characters) of
the `## Sources` row that names it. The checks below treat the three alike.

1. Every token written like a web id (`web-`, `web_` or `web` and 6 or more hex digits) must be
   exactly `web-` and 12 hex digits and a retained page, wherever it appears; any other is reported
   as an unknown web source id.
2. Every page cited anywhere, by id or URL, has a `## Sources` row that names it.
3. Every URL in a `## Sources` row must have been fetched in this run (compared after normalising
   scheme and host case, `:443`, fragment, an empty query and one trailing `/`; `http` is never
   `https`). Both the URL and the final URL of every retained row count. A URL with a user name or
   password is refused at fetch (`webfetch._problem`), so it is never retained.
4. A `## Sources` row that names a web id or URL needs a Source type cell: one allowed type,
   optionally followed by `;` and a Later event or Undated label (`Issuer filing; Later event`);
   this check is `web_source_issues` in `handoff.py`.
5. A row for a later-event page must carry the words Later event (or `later-event`) and a row for
   an undated page the word Undated, in any case, in the stated-date cell or after the Source type;
   `## Gaps` must name an undated page's id. Two URLs that serve the same bytes share one id; the
   strictest status of its index rows applies (later-event over undated over usable).
6. TDR.6 rows are the table rows under a heading naming TDR.6 (`TDR` then an optional space, dot or
   hyphen, then 6; until a heading of the same or higher level) and any row whose first cell is
   `<peer>.<operand>` (revenue, ebitda, debt, interest, ffo). Such a row must cite no later-event
   page, by id, URL, `## Sources` title or through rows linked by a shared first cell, followed to
   the end (an `evidence_id` pointing at a register row that points at the page). Any URL in it
   must have been fetched. Inside a TDR.6 section every line counts, table or not: no line may
   cite a later-event page.
7. A TDR.6 row that cites a page must carry a quote (the cell under a `quote` header, or the longest
   cell; a trailing page reference in brackets and the surrounding quote marks are dropped), the
   quote must appear in the text of a page the row cites, and when the table has an `amount`
   header, the amount cell's text must appear inside the quote.
8. In a paragraph (consecutive non-blank lines that are not table rows or headings) and in a table
   row that cites a page, every quoted span of 12 or more characters must appear in one of the pages
   it cites. A span runs from any of `" “ ” „ « » ‹ ›` to the next of them (mixed pairs count; a
   mark right after a digit is an inch mark and opens nothing) after HTML entities are unescaped,
   or between single quotes where the opening follows a non-word character (not `'24`) and the
   closing precedes one. Straight and curly apostrophes are one character on both sides.

Known limit of check 8, a consequence of the rule: a paragraph or row that cites a web page may
quote only from the pages it cites. One that mixes a web source with a quoted issuer-file passage of
12 or more characters is rejected and must be split. `WEB_LOOKUP_RULES` states this. An apostrophe
pair that looks like a single-quoted span can be rejected; it is rephrased.

Inherent limits of a mechanical check. These are governed by instruction in `WEB_LOOKUP_RULES`, not
caught mechanically: a page cited by a scheme-less address, a bare id without `web-`, or a
description; quoted spans under 12 characters; a figure split across short quotes; Markdown
blockquotes (`> passage`); paraphrase without quote marks; later-event figures in prose outside
TDR.6; a TDR.6 row whose evidence is linked only through a non-first column, or a TDR.6 table under a
sibling heading of the same level; SEC facts filed after the cutoff.

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
`off`: the launcher resolves `default` first.

This is separate from hosted `web_search` (ruling-gated, OpenAI only, offered to public and private
cases; ruling 2026-11-11-run-start-submit.md), which is unchanged. Both may be on in one run, and
the module is told which tools it has.

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
4. The run-start page's approved summary does not show the Lookup line, although lookup is on by
   default for public cases started there.
5. A resumed run rechecks retained responses without the web checks.
6. URLs that carry run material are flagged by event, not refused.
7. CP-4's runbook describes an EDGAR acquisition lane. CP-4 was not given the tools.
8. `handoff._pages` parses issuer PDFs with the same PDF library and no exception handling. This
   predates this work.
9. The change is over the global 800-line guideline (about 4,950 changed lines since the first
   commit; most of it tests).
10. Search API: the owner chose it as the next step; not built.
