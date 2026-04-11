const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  ExternalHyperlink
} = require('docx');
const fs = require('fs');

// ── Brand colours (mirrors compiler.py) ──────────────────────────────────────
const NAVY   = "1A3A5C";
const GOLD   = "C9A84C";
const WHITE  = "FFFFFF";
const LIGHT  = "F8F7F4";
const GRAY   = "555555";
const GREEN  = "2E7D32";
const AMBER  = "E65100";
const RED    = "C62828";

// ── Helpers ───────────────────────────────────────────────────────────────────
const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: "DDDDDD" };
const borders    = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
const noBorder   = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders  = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, bold: true, size: 36, color: NAVY, font: "Arial" })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 80 },
    children: [new TextRun({ text, bold: true, size: 28, color: NAVY, font: "Arial" })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text, bold: true, size: 24, color: GRAY, font: "Arial" })],
  });
}
function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", ...opts })],
  });
}
function bodyRuns(runs) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: runs.map(r => new TextRun({ size: 22, font: "Arial", ...r })),
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, font: "Arial" })],
  });
}
function code(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { fill: "F0F0F0", type: ShadingType.CLEAR },
    indent: { left: 360 },
    children: [new TextRun({ text, size: 18, font: "Courier New", color: "333333" })],
  });
}
function divider() {
  return new Paragraph({
    spacing: { before: 160, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: GOLD, space: 1 } },
    children: [],
  });
}
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function label(text, color = NAVY) {
  return new TextRun({ text, bold: true, size: 22, font: "Arial", color });
}
function normal(text) {
  return new TextRun({ text, size: 22, font: "Arial" });
}
function mono(text) {
  return new TextRun({ text, size: 19, font: "Courier New", color: "333333" });
}

// ── Table builders ────────────────────────────────────────────────────────────
function headerRow(cells, colWidths) {
  return new TableRow({
    tableHeader: true,
    children: cells.map((text, i) =>
      new TableCell({
        borders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text, bold: true, size: 20, color: WHITE, font: "Arial" })],
        })],
      })
    ),
  });
}
function dataRow(cells, colWidths, shaded = false) {
  return new TableRow({
    children: cells.map((content, i) =>
      new TableCell({
        borders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: shaded ? "F8F7F4" : WHITE, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: Array.isArray(content)
            ? content
            : [new TextRun({ text: String(content), size: 20, font: "Arial" })],
        })],
      })
    ),
  });
}
function simpleTable(headers, rows, colWidths) {
  return new Table({
    width: { size: colWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      headerRow(headers, colWidths),
      ...rows.map((r, i) => dataRow(r, colWidths, i % 2 === 0)),
    ],
  });
}

// ── Accent box (navy left border) ─────────────────────────────────────────────
function accentBox(paragraphs, fill = "EEF2F7") {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [120, 9240],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: noBorders,
          width: { size: 120, type: WidthType.DXA },
          shading: { fill: NAVY, type: ShadingType.CLEAR },
          children: [new Paragraph({ children: [] })],
        }),
        new TableCell({
          borders: noBorders,
          width: { size: 9240, type: WidthType.DXA },
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 120, bottom: 120, left: 200, right: 120 },
          children: paragraphs,
        }),
      ],
    })],
  });
}

// ────────────────────────────────────────────────────────────────────────────
// DOCUMENT
// ────────────────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u00B7",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }, {
        level: 1, format: LevelFormat.BULLET, text: "-",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
      }],
    }],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 280, after: 80 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: GRAY },
        paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: GOLD, space: 4 } },
          children: [
            new TextRun({ text: "ACC Campaign Agent  ", bold: true, size: 18, font: "Arial", color: NAVY }),
            new TextRun({ text: "Brand Voice & Styling Reference", size: 18, font: "Arial", color: GRAY }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: GOLD, space: 4 } },
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "Page ", size: 18, font: "Arial", color: GRAY }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: GRAY }),
            new TextRun({ text: " of ", size: 18, font: "Arial", color: GRAY }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "Arial", color: GRAY }),
          ],
        })],
      }),
    },
    children: [

      // ── COVER ────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 1440, after: 120 },
        children: [new TextRun({ text: "ACC Campaign Agent", bold: true, size: 64, font: "Arial", color: NAVY })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 80 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: GOLD, space: 6 } },
        children: [new TextRun({ text: "Brand Voice & Styling — Technical Reference", size: 36, font: "Arial", color: GOLD })],
      }),
      new Paragraph({ spacing: { before: 240, after: 80 }, children: [new TextRun({ text: "Version 1.0  |  Marriott Bonvoy  |  April 2026", size: 22, font: "Arial", color: GRAY })] }),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [new TextRun({ text: "Multi-agent Adobe Campaign Classic pipeline powered by Claude", size: 22, font: "Arial", color: GRAY, italics: true })] }),

      pageBreak(),

      // ── SECTION 1: OVERVIEW ──────────────────────────────────────────────
      h1("1.  How Brand Identity Flows Through the Pipeline"),
      body("Brand voice and visual styling are not applied at a single point. They are baked into every stage of the pipeline — from how the brief is read, to the angles generated, the copy written, the QA score awarded, and finally the HTML compiled. The diagram below shows where each element enters."),

      new Paragraph({ spacing: { before: 200, after: 100 }, children: [] }),

      simpleTable(
        ["Pipeline Stage", "Brand Input", "What It Controls"],
        [
          ["Stage 1 · Brief Strategist",       "BRAND_VOICE.tone, .avoid",                       "Sets the tone enum for the entire campaign (aspirational, warm, etc.)"],
          ["Stage 3 · Content Strategist",     "BRAND_VOICE.tone, .prefer, .avoid",              "Shapes which messaging angles are generated and how they are framed"],
          ["Stage 5 · Content Author",         "BRAND_VOICE.tone, .prefer, .avoid + CONTENT_RULES", "System prompt bakes brand rules directly into copywriting instructions"],
          ["Stage 7 · Content Critic",         "BRAND_VOICE.tone, .avoid",                       "Scores content against brand alignment; drops below 70 block the gate"],
          ["Stage 10 · Compiler",              "Hard-coded brand colours + module CSS",          "Renders HTML email with Marriott Bonvoy navy/gold visual identity"],
        ],
        [2600, 3200, 3560]
      ),

      divider(),

      // ── SECTION 2: BRAND VOICE CONFIG ───────────────────────────────────
      h1("2.  Brand Voice Configuration"),
      body("All brand voice rules live in a single Python dict inside config.py. This is the single source of truth — change it here and all agents pick it up automatically on the next run."),

      h2("2.1  The BRAND_VOICE Dictionary"),

      accentBox([
        new Paragraph({ spacing: { before: 80, after: 40 }, children: [new TextRun({ text: "config.py", bold: true, size: 18, font: "Courier New", color: GOLD })] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('BRAND_VOICE = {')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "Marriott Bonvoy": {')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('        "tone":     "aspirational, warm, rewarding",')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('        "avoid":    ["pushy", "salesy", "cheap", "discount"],')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('        "prefer":   ["exclusive", "curated", "earned", "experience", "points"],')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('        "sign_off": "The Marriott Bonvoy Team",')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    }')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('}') ]}),
      ], "F0F4F8"),

      new Paragraph({ spacing: { before: 160, after: 60 }, children: [] }),

      simpleTable(
        ["Key", "Value", "Purpose"],
        [
          ["tone",     '"aspirational, warm, rewarding"',                   "Passed into every LLM system prompt as the required voice register"],
          ["avoid",    '["pushy","salesy","cheap","discount"]',             "The Content Author is instructed never to use these words; the Content Critic penalises them"],
          ["prefer",   '["exclusive","curated","earned","experience","points"]', "Words the Content Author is instructed to reach for naturally"],
          ["sign_off", '"The Marriott Bonvoy Team"',                       "Used in email footer; not yet wired to compiler — available for extension"],
        ],
        [1800, 3400, 4160]
      ),

      h2("2.2  Adding a New Brand"),
      body("To onboard a second brand (e.g. W Hotels, St. Regis), add a new entry to BRAND_VOICE and pass the correct brand name in the CampaignBrief. Every agent resolves its brand context via brand_ctx = BRAND_VOICE.get(brief.brand, {}) — no other changes required."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono('"W Hotels": {')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "tone":   "bold, irreverent, design-forward",')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "avoid":  ["traditional", "classic", "timeless"],')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "prefer": ["whatever/whenever", "living", "bold"],')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "sign_off": "W Hotels",')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('}') ]}),
      ], "F0F4F8"),

      divider(),

      // ── SECTION 3: STAGE-BY-STAGE APPLICATION ───────────────────────────
      h1("3.  Stage-by-Stage: How Brand Voice Is Applied"),

      h2("3.1  Stage 1 — Brief Strategist"),
      body("The Brief Strategist is the first agent that touches brand context. It reads BRAND_VOICE for the brand named in the brief and includes tone and avoid in the user message sent to Claude."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono("# agents/brief_strategist.py")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("brand_ctx = BRAND_VOICE.get(brief.brand, {})")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('user = f"""')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('Brand voice: {brand_ctx.get("tone", "aspirational")}')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('Avoid: {brand_ctx.get("avoid", [])}')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('"""')] }),
      ], "F0F4F8"),

      body("The model uses this context to select the correct tone enum (aspirational | urgent | warm | celebratory | reactivation) which is then stored on the StructuredBrief and passed to every downstream agent."),

      h2("3.2  Stage 3 — Content Strategist"),
      body("The Content Strategist generates 3–5 messaging angles. It receives the full brand voice context including preferred vocabulary and words to avoid. Each angle it generates must sit within the brand register, which is why you never see a Marriott Bonvoy angle described as cheap or discount-led."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono("# agents/content_strategist.py — user message")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Brand voice: {brand_ctx.get('tone', 'aspirational')}")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Prefer words like: {brand_ctx.get('prefer', [])}")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Avoid: {brand_ctx.get('avoid', [])}")] }),
      ], "F0F4F8"),

      h2("3.3  Stage 5 — Content Author"),
      body("This is where brand voice has the deepest impact. The Content Author's system prompt is dynamically built from four brand variables baked directly into the copywriting instruction set the model sees before writing a single word."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono("# The system prompt the model receives:")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("You are a luxury email copywriter for Marriott Bonvoy.")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Tone:              aspirational, warm, rewarding")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Brand:             Marriott Bonvoy")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Prefer words like: ['exclusive','curated','earned','experience','points']")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("Avoid:             ['pushy','salesy','cheap','discount']")] }),
      ], "F0F4F8"),

      body("The model does not receive a generic copywriting prompt — it receives a Marriott Bonvoy-specific prompt every time. Subject line, preheader, hero headline, body copy, tile headlines, and CTA label are all written under this instruction set."),

      h2("3.4  Stage 7 — Content Critic"),
      body("The Content Critic evaluates the output against brand alignment as one of its six scoring dimensions. It also receives brand_voice and avoid so it can penalise any copy that violates the brand register, even if the lint layer passed."),

      simpleTable(
        ["Scoring Dimension", "Brand Impact"],
        [
          ["Subject line effectiveness",   "Penalises generic or off-tone subjects"],
          ["Brand voice alignment",        "Direct scoring against aspirational/warm/rewarding register; vocabulary check against avoid list"],
          ["Module flow",                  "Hero-to-CTA narrative arc must feel consistent with the brand experience"],
          ["Personalization quality",      "Checks that tokens are used naturally, not mechanically"],
          ["CTA clarity and urgency",      "Luxury brand CTAs should feel inviting not pressuring"],
          ["Brief alignment",              "Ensures the copy delivers on the angle and campaign intent"],
        ],
        [3200, 6160]
      ),

      body("A score below 70 triggers a gate failure. The blocking issue is surfaced in the HITL panel so a reviewer can decide whether to approve with override or reject for a rewrite."),

      divider(),

      // ── SECTION 4: HTML BRAND STYLING ───────────────────────────────────
      pageBreak(),
      h1("4.  HTML Email Brand Styling"),
      body("The compiler (python/compiler.py) applies a fixed Marriott Bonvoy visual identity to every compiled email. The styling is hardcoded in the compiler — it does not change per campaign — ensuring visual consistency regardless of LLM output."),

      h2("4.1  Colour Palette"),

      simpleTable(
        ["Token", "Hex", "Usage in Email"],
        [
          ["Navy",      "#1A3A5C",  "Header bar background, hero background, heading text, tile headlines, greeting text, CTA hover"],
          ["Gold",      "#C9A84C",  "Header bar text (brand name), CTA button background, letter-spacing accent"],
          ["White",     "#FFFFFF",  "Email body background, header bar text on CTA"],
          ["Off-white", "#F5F5F0",  "Page background behind the email container"],
          ["Dark grey", "#444444",  "Body copy inside greeting, tile, and body modules"],
          ["Light grey","#999999",  "Footer copy, unsubscribe link"],
          ["Rule",      "#EEEEEE",  "Border-bottom separator between tile modules"],
        ],
        [1800, 1400, 6160]
      ),

      h2("4.2  Typography"),
      simpleTable(
        ["Element", "Font", "Size", "Style"],
        [
          ["Body/container",  "Georgia, serif",  "—",    "Base font stack — serif for luxury feel"],
          ["Hero headline",   "Georgia, serif",  "28px", "font-weight: normal (not bold — refined)"],
          ["Greeting",        "Georgia, serif",  "18px", "color: #1A3A5C"],
          ["Body copy",       "Georgia, serif",  "—",    "color: #444"],
          ["Header bar",      "system default",  "13px", "letter-spacing: 2px; text-transform: uppercase"],
          ["CTA label",       "system default",  "14px", "letter-spacing: 1px; text-transform: uppercase"],
          ["Footer",          "system default",  "11px", "color: #999"],
        ],
        [2200, 2200, 1400, 3560]
      ),

      h2("4.3  Email Module Structure"),
      body("Every compiled email follows the same table-based structure. Modules are rendered in the order the Content Author defined them, sandwiched between a fixed header bar and a fixed footer."),

      simpleTable(
        ["Zone", "Background", "Content", "Fixed or Dynamic"],
        [
          ["Header bar",   "#1A3A5C / gold text",  "Brand name (uppercase, letter-spaced)",  "Fixed — always present"],
          ["Hero",         "#1A3A5C",               "Headline + body_copy from hero module",  "Dynamic — LLM content"],
          ["Greeting",     "white",                 "Personalised greeting headline + copy",  "Dynamic — LLM content"],
          ["Tiles",        "white + #eee border",   "Benefit tiles (headline + copy per tile)","Dynamic — LLM content"],
          ["Body",         "white",                 "Supporting body copy",                   "Dynamic — LLM content"],
          ["CTA",          "white",                 "Gold button (#C9A84C) with label",       "Dynamic — LLM content"],
          ["Footer",       "white",                 "Membership note + unsubscribe link",     "Fixed — always present"],
        ],
        [1800, 2200, 3000, 2360]
      ),

      divider(),

      // ── SECTION 5: CONTENT RULES (deterministic enforcement) ────────────
      h1("5.  Content Rules — Deterministic Enforcement"),
      body("Brand voice from the LLM is checked by a deterministic Python linter (python/content_lint.py) before any gate evaluation. These rules enforce hard constraints that the LLM cannot override."),

      h2("5.1  Rules Table"),
      simpleTable(
        ["Rule", "Value", "Enforced By", "Gate Impact"],
        [
          ["Subject line max chars",    "60",                    "content_lint.py",  "Hard fail — blocks gate"],
          ["Preheader max chars",       "90",                    "content_lint.py",  "Hard fail — blocks gate"],
          ["CTA label max chars",       "35",                    "content_lint.py",  "Hard fail — blocks gate"],
          ["Minimum modules",           "3",                     "content_lint.py",  "Hard fail — blocks gate"],
          ["Required module types",     "hero, cta",             "content_lint.py",  "Hard fail — blocks gate"],
          ["Max word count",            "350",                   "content_lint.py",  "Warning only — does not block"],
          ["Required tokens",           "[] (configurable)",     "content_lint.py",  "Hard fail if token list populated"],
          ["Critic score threshold",    "70 / 100",              "gate_aggregator.py","Hard fail — blocks gate"],
        ],
        [2600, 2000, 2000, 2760]
      ),

      h2("5.2  Where to Change the Rules"),
      body("All values live in config.py under CONTENT_RULES and GATE_THRESHOLDS. No code change is needed — edit the dict and restart."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono("# config.py")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("CONTENT_RULES = {")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "subject_max_chars":   60,')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "preheader_max_chars": 90,')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "cta_max_chars":        35,')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "required_tokens":     [],   # e.g. ["{{first_name}}"]')] }),
        new Paragraph({ spacing: { before: 0, after: 40 }, children: [mono('}')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("GATE_THRESHOLDS = {")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "min_workflow_critic_score": 70,')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('    "min_content_critic_score":  70,')] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono('}')] }),
      ], "F0F4F8"),

      divider(),

      // ── SECTION 6: TOKEN PERSONALISATION ────────────────────────────────
      pageBreak(),
      h1("6.  Personalisation & Token Resolver"),
      body("The Variant Preview in the UI simulates how the email renders for different Bonvoy member tiers. A Python token resolver (python/variants.py) replaces placeholder tokens in the compiled HTML with persona-specific values before rendering."),

      h2("6.1  Supported Tokens"),
      simpleTable(
        ["Token Format", "Source Field", "Fallback"],
        [
          ["{{first_name}}",                    "FirstName",                          '"Valued Member"'],
          ["{{last_name}}",                     "LastName",                           '""'],
          ["{{points_balance}}",                "_RECIPIENT_TOTAL_POINT_BALANCE",     '"your points"'],
          ["{{tier}}",                          "_RECIPIENT_SERVLEVEL_LABEL",         '"Member"'],
          ["{{bonvoy_number}}",                 "masked in preview",                  '"XXXXXXXX"'],
          ["@@ObloyaltyLevel@@",                "_RECIPIENT_SERVLEVEL_CODE",          '"M"'],
          ["@@ObloyaltySummary@@",              "_RECIPIENT_TOTAL_POINT_BALANCE",     '"your points"'],
          ["@@marriottDeliveryPersonalizedHeader@@", "stripped in preview",           '""'],
        ],
        [2800, 3200, 3360]
      ),

      h2("6.2  Member Tier Variants"),
      body("The UI ships with 6 common variants and 2 edge cases designed to stress-test all personalization branches."),

      simpleTable(
        ["Variant", "Tier Code", "Points", "Tests"],
        [
          ["Member — Has Points Balance",      "M",  "4,200",   "Standard path: firstName + points both present"],
          ["Silver Elite — Moderate Points",   "S",  "12,500",  "Mid-tier messaging branch"],
          ["Gold Elite — High Points Balance", "G",  "38,750",  "Primary target segment — core conversion path"],
          ["Platinum Elite — Strong Points",   "P",  "87,200",  "High-frequency traveller tone"],
          ["Titanium Elite — No Points Data",  "A",  "(empty)", "Points-absent fallback branch"],
          ["Ambassador Elite — Premium Points","PP", "245,000", "VIP/ultra-high-value treatment"],
          ["EDGE: No First Name",              "M",  "3,100",   "Greeting fallback — must not render raw token"],
          ["EDGE: No Name, No Points",         "S",  "(empty)", "Worst-case double-fallback"],
        ],
        [3000, 1400, 1400, 3560]
      ),

      h2("6.3  How Token Resolution Works"),
      body("When a variant is selected in the UI, the compiled HTML from the pipeline is passed through resolve_tokens() before rendering in the Simulated Preview tab. The Raw Tokens (ACC) tab shows the original HTML with tokens highlighted — yellow for {{handlebars}}, orange for @@ACC tokens@@."),

      accentBox([
        new Paragraph({ spacing: { before: 40, after: 20 }, children: [mono("# python/variants.py")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("def resolve_tokens(html: str, variant_data: dict) -> str:")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("    for token, resolver in TOKEN_MAP.items():")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("        result = result.replace(token, resolver(variant_data))")] }),
        new Paragraph({ spacing: { before: 0, after: 20 }, children: [mono("    # Regex fallback strips any remaining {{token}} gracefully")] }),
      ], "F0F4F8"),

      divider(),

      // ── SECTION 7: SUMMARY ───────────────────────────────────────────────
      h1("7.  Summary — Layers of Brand Control"),
      body("Brand identity in the ACC Campaign Agent operates across three distinct layers:"),

      simpleTable(
        ["Layer", "Type", "File", "Controls"],
        [
          ["Brand Voice",      "LLM instruction",         "config.py → agents/*",           "Tone, preferred vocabulary, banned words — baked into every agent system prompt"],
          ["Content Rules",    "Deterministic enforcement","config.py → python/content_lint.py","Hard character limits, required modules, mandatory tokens — cannot be overridden by the LLM"],
          ["HTML Styling",     "Fixed CSS",               "python/compiler.py",             "Colour palette, typography, module layout — applied identically to every compiled email"],
          ["Personalization",  "Token resolution",        "python/variants.py",             "Member-specific field injection at preview/delivery time — decoupled from content generation"],
        ],
        [1800, 2200, 2800, 2560]
      ),

      new Paragraph({ spacing: { before: 240, after: 120 }, children: [] }),

      accentBox([
        new Paragraph({ spacing: { before: 80, after: 40 }, children: [new TextRun({ text: "Key principle", bold: true, size: 22, font: "Arial", color: NAVY })] }),
        new Paragraph({ spacing: { before: 0, after: 80 }, children: [new TextRun({ text: "Brand voice rules are applied via LLM instruction — they shape, but cannot guarantee, output. Content rules are applied deterministically — they enforce, regardless of LLM output. Both layers must pass before a campaign reaches the human reviewer.", size: 22, font: "Arial", color: "333333", italics: true })] }),
      ], "FFFDE7"),

    ],
  }],
});

// ── Write ─────────────────────────────────────────────────────────────────────
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("ACC_Campaign_Agent_Brand_Voice.docx", buffer);
  console.log("Done: ACC_Campaign_Agent_Brand_Voice.docx");
});
