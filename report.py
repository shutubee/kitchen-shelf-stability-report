from typing import Dict, Any
import pandas as pd


def build_summary_text(project_name: str, shelf_summary: Dict[str, Any]) -> str:
    return (
        f"# {project_name}\n\n"
        f"Member count: {shelf_summary.get('member_count', 0)}\n"
        f"Max risk score: {shelf_summary.get('max_total_score', 0):.3f}\n"
        f"Mean risk score: {shelf_summary.get('mean_total_score', 0):.3f}\n"
        f"Governing member: {shelf_summary.get('governing_member')}\n"
        f"Risk band: {shelf_summary.get('risk_band')}\n\n"
        f"Interpretation: {shelf_summary.get('note', '')}\n"
    )


def build_report_markdown(
    project_name: str,
    config: Dict[str, Any],
    results_df: pd.DataFrame,
    shelf_summary: Dict[str, Any],
) -> str:
    md = []
    md.append(build_summary_text(project_name, shelf_summary))
    md.append("## Configuration\n")
    md.append(f"- Material: {config.get('material_name')}\n")
    md.append(f"- Boundary: {config.get('boundary', {}).get('name')}\n")
    md.append(f"- Geometry: {config.get('geometry', {}).get('name')}\n")
    md.append(f"- Load: {config.get('load', {}).get('name')}\n")
    md.append("\n## Member Results\n")
    md.append(results_df.to_markdown(index=False))
    md.append("\n")
    return "\n".join(md)


def results_to_csv_bytes(results_df: pd.DataFrame) -> bytes:
    return results_df.to_csv(index=False).encode("utf-8")
