"""
Compiler + Validator — assembles the final ACC-ready package.
Generates workflow XML and email HTML, then validates the output.
"""

import os
import json
import datetime
from pathlib import Path
from models.campaign import CampaignPackage
from models.workflow import WorkflowStep


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


# ---------------------------------------------------------------------------
# XML compiler — ACC workflow format
# ---------------------------------------------------------------------------

def compile_workflow_xml(package: CampaignPackage) -> str:
    wf = package.workflow
    steps_xml = "\n".join(_step_to_xml(s) for s in wf.steps)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<workflow id="{wf.workflow_id}" label="{wf.campaign_name}">
  <targeting>
    <![CDATA[
      SELECT * FROM nms:recipient
      WHERE {wf.targeting_sql}
    ]]>
  </targeting>
  <steps>
{steps_xml}
  </steps>
  <entry_signal>{wf.entry_signal}</entry_signal>
  <exit_signal>{wf.exit_signal}</exit_signal>
  <description>{wf.description}</description>
</workflow>"""


def _step_to_xml(step: WorkflowStep) -> str:
    attrs = f'id="{step.step_id}" type="{step.step_type}" label="{step.label}"'
    inner = ""
    if step.condition:
        inner += f"\n      <condition><![CDATA[{step.condition}]]></condition>"
    if step.wait_days:
        inner += f"\n      <wait days=\"{step.wait_days}\"/>"
    if step.step_type == "delivery":
        inner += f"\n      <channel>{step.channel}</channel>"
    return f"    <step {attrs}>{inner}\n    </step>"


# ---------------------------------------------------------------------------
# HTML compiler — email body
# ---------------------------------------------------------------------------

def compile_email_html(package: CampaignPackage) -> str:
    content = package.content
    brand = package.brief.raw.brand
    modules_html = "\n".join(_module_to_html(m) for m in content.modules)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{content.subject_line}</title>
</head>
<body style="margin:0;padding:0;font-family:Georgia,serif;background:#f5f5f0;">
  <!-- PREHEADER -->
  <span style="display:none;max-height:0;overflow:hidden;">{content.preheader}</span>

  <table width="600" align="center" cellpadding="0" cellspacing="0"
         style="background:#ffffff;margin:20px auto;">
    <tr>
      <td style="padding:16px 24px;background:#1a3a5c;color:#c9a84c;
                 font-size:13px;letter-spacing:2px;text-transform:uppercase;">
        {brand}
      </td>
    </tr>
{modules_html}
    <tr>
      <td style="padding:16px 24px;font-size:11px;color:#999;text-align:center;">
        You are receiving this email as a {brand} member.<br>
        <a href="%%unsubscribe_url%%" style="color:#999;">Unsubscribe</a>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _module_to_html(module) -> str:
    t = module.module_type
    if t == "hero":
        return f"""    <tr>
      <td style="padding:40px 24px;background:#1a3a5c;color:#ffffff;text-align:center;">
        <h1 style="margin:0;font-size:28px;font-weight:normal;">{module.headline}</h1>
        <p style="margin:12px 0 0;">{module.body_copy}</p>
      </td>
    </tr>"""
    elif t == "greeting":
        return f"""    <tr>
      <td style="padding:24px 24px 8px;">
        <p style="font-size:18px;color:#1a3a5c;">{module.headline}</p>
        <p style="color:#444;">{module.body_copy}</p>
      </td>
    </tr>"""
    elif t == "tile":
        return f"""    <tr>
      <td style="padding:16px 24px;border-bottom:1px solid #eee;">
        <strong style="color:#1a3a5c;">{module.headline}</strong>
        <p style="color:#444;margin:4px 0;">{module.body_copy}</p>
      </td>
    </tr>"""
    elif t == "cta":
        return f"""    <tr>
      <td style="padding:32px 24px;text-align:center;">
        <a href="{module.cta_url or '#'}"
           style="background:#c9a84c;color:#ffffff;padding:14px 32px;
                  text-decoration:none;font-size:14px;letter-spacing:1px;
                  text-transform:uppercase;">{module.cta_label}</a>
      </td>
    </tr>"""
    else:
        return f"""    <tr>
      <td style="padding:16px 24px;">
        <p style="color:#444;">{module.body_copy}</p>
      </td>
    </tr>"""


# ---------------------------------------------------------------------------
# Validate compiled output
# ---------------------------------------------------------------------------

def validate_output(xml: str, html: str) -> dict:
    issues = []
    if "<?xml" not in xml:
        issues.append("Compiled XML missing declaration.")
    if "<workflow" not in xml:
        issues.append("Compiled XML missing <workflow> root.")
    if "<body" not in html:
        issues.append("Compiled HTML missing <body> tag.")
    if "%%unsubscribe_url%%" not in html:
        issues.append("Compiled HTML missing unsubscribe link.")
    return {"passed": len(issues) == 0, "issues": issues}


# ---------------------------------------------------------------------------
# Write output files
# ---------------------------------------------------------------------------

def compile_and_save(package: CampaignPackage) -> CampaignPackage:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = package.brief.raw.campaign_name.replace(" ", "_") or package.campaign_id

    xml = compile_workflow_xml(package)
    html = compile_email_html(package)
    validation = validate_output(xml, html)

    if not validation["passed"]:
        package.errors.extend(validation["issues"])

    xml_path  = OUTPUT_DIR / f"{safe_name}_{ts}_workflow.xml"
    html_path = OUTPUT_DIR / f"{safe_name}_{ts}_email.html"
    json_path = OUTPUT_DIR / f"{safe_name}_{ts}_package.json"

    xml_path.write_text(xml, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    # Serialize package summary
    summary = {
        "campaign_id":   package.campaign_id,
        "campaign_name": package.brief.raw.campaign_name,
        "angle":         package.selected_angle.name,
        "subject":       package.content.subject_line,
        "gate_passed":   package.gate_passed,
        "hitl_approved": package.hitl_approved,
        "approved_by":   package.approved_by,
        "approved_at":   package.approved_at,
        "errors":        package.errors,
        "workflow_xml":  str(xml_path),
        "email_html":    str(html_path),
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    package.compiled_xml   = xml
    package.compiled_html  = html
    package.output_path    = str(json_path)
    return package
