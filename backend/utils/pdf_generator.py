import os
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from utils.logger import setup_logger

logger = setup_logger("pdf_generator", "logs/reports.log")


class PDFReportGenerator:
    """
    Generates professional PDF reports for RansomGuard.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Title"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=12,
            alignment=TA_CENTER,
        )

        self.subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=self.styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#16213e"),
            spaceAfter=6,
            alignment=TA_CENTER,
        )

        self.heading_style = ParagraphStyle(
            "CustomHeading",
            parent=self.styles["Heading1"],
            fontSize=14,
            textColor=colors.HexColor("#0f3460"),
            spaceBefore=16,
            spaceAfter=8,
        )

        self.section_style = ParagraphStyle(
            "SectionStyle",
            parent=self.styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#533483"),
            spaceBefore=12,
            spaceAfter=6,
        )

        self.body_style = ParagraphStyle(
            "BodyStyle",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        )

        self.warning_style = ParagraphStyle(
            "WarningStyle",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#c0392b"),
            spaceBefore=4,
            spaceAfter=4,
        )

    def generate_threat_report(
        self,
        output_path: str,
        threats: List[Dict[str, Any]],
        system_info: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        title: str = "RansomGuard Threat Report",
    ) -> bool:
        """
        Generate a PDF threat report.

        Args:
            output_path: Output file path
            threats: List of threat log dictionaries
            system_info: System information dictionary
            start_date: Report start date
            end_date: Report end date
            title: Report title

        Returns:
            True if successful
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )

            story = []

            # Title Section
            story.append(Paragraph("🛡️ RansomGuard", self.title_style))
            story.append(Paragraph(title, self.subtitle_style))
            story.append(
                Paragraph(
                    f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    self.subtitle_style,
                )
            )
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460")))
            story.append(Spacer(1, 0.2 * inch))

            # Report Period
            if start_date or end_date:
                period_text = "Report Period: "
                if start_date:
                    period_text += f"{start_date.strftime('%Y-%m-%d')}"
                if end_date:
                    period_text += f" to {end_date.strftime('%Y-%m-%d')}"
                story.append(Paragraph(period_text, self.body_style))
                story.append(Spacer(1, 0.1 * inch))

            # Executive Summary
            story.append(Paragraph("Executive Summary", self.heading_style))

            total_threats = len(threats)
            critical_count = sum(1 for t in threats if t.get("threat_level") == "critical")
            high_count = sum(1 for t in threats if t.get("threat_level") == "high")
            medium_count = sum(1 for t in threats if t.get("threat_level") == "medium")
            ransomware_count = sum(1 for t in threats if t.get("is_ransomware"))
            active_count = sum(1 for t in threats if t.get("status") == "active")
            resolved_count = sum(1 for t in threats if t.get("status") == "resolved")

            summary_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Total Threats", str(total_threats), "Critical Threats", str(critical_count)],
                ["High Severity", str(high_count), "Medium Severity", str(medium_count)],
                ["Ransomware Detected", str(ransomware_count), "Active Threats", str(active_count)],
                ["Resolved Threats", str(resolved_count), "Report Generated", datetime.utcnow().strftime("%H:%M UTC")],
            ]

            summary_table = Table(summary_data, colWidths=[1.8 * inch, 1.2 * inch, 1.8 * inch, 1.2 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(summary_table)
            story.append(Spacer(1, 0.2 * inch))

            # System Information Section
            if system_info:
                story.append(Paragraph("System Information", self.heading_style))

                sys_data = [
                    ["Property", "Value"],
                    ["Hostname", system_info.get("hostname", "N/A")],
                    ["Platform", system_info.get("platform", "N/A")],
                    ["Architecture", system_info.get("architecture", "N/A")],
                    ["CPU Usage", f"{system_info.get('cpu_percent', 'N/A')}%"],
                    ["Memory Usage", f"{system_info.get('memory_percent', 'N/A')}%"],
                    ["Uptime", system_info.get("uptime", "N/A")],
                ]

                sys_table = Table(sys_data, colWidths=[2.5 * inch, 4.5 * inch])
                sys_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#533483")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("ALIGN", (0, 0), (0, -1), "LEFT"),
                            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f0ff")]),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                            ("PADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(sys_table)
                story.append(Spacer(1, 0.2 * inch))

            # Threat Details Section
            story.append(Paragraph("Threat Details", self.heading_style))

            if threats:
                threat_data = [
                    ["#", "File", "Threat Level", "Confidence", "Risk Score", "Status", "Timestamp"],
                ]

                for idx, threat in enumerate(threats[:50], 1):  # Limit to 50 for PDF
                    file_name = threat.get("file_name", "Unknown")
                    if len(file_name) > 25:
                        file_name = file_name[:22] + "..."

                    timestamp = threat.get("timestamp", "")
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.strftime("%m/%d %H:%M")
                    elif isinstance(timestamp, str) and "T" in timestamp:
                        timestamp = timestamp[:16].replace("T", " ")

                    threat_data.append(
                        [
                            str(idx),
                            file_name,
                            threat.get("threat_level", "N/A").upper(),
                            f"{float(threat.get('confidence', 0)) * 100:.1f}%",
                            f"{float(threat.get('risk_score', 0)):.1f}",
                            threat.get("status", "N/A"),
                            str(timestamp)[:16],
                        ]
                    )

                threat_table = Table(
                    threat_data,
                    colWidths=[0.3 * inch, 2.0 * inch, 1.0 * inch, 0.9 * inch, 0.8 * inch, 0.9 * inch, 1.1 * inch],
                )

                threat_style = TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTSIZE", (0, 1), (-1, -1), 7),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                        ("PADDING", (0, 0), (-1, -1), 4),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )

                # Color-code threat levels
                for row_idx, threat in enumerate(threats[:50], 1):
                    level = threat.get("threat_level", "")
                    color = colors.white
                    if level == "critical":
                        color = colors.HexColor("#ffe0e0")
                    elif level == "high":
                        color = colors.HexColor("#fff0e0")
                    elif level == "medium":
                        color = colors.HexColor("#fffde0")

                    if level in ["critical", "high", "medium"]:
                        threat_style.add("BACKGROUND", (0, row_idx), (-1, row_idx), color)

                threat_table.setStyle(threat_style)
                story.append(threat_table)

                if len(threats) > 50:
                    story.append(Spacer(1, 0.1 * inch))
                    story.append(
                        Paragraph(
                            f"Note: Showing 50 of {len(threats)} total threats. Download CSV for complete data.",
                            self.body_style,
                        )
                    )
            else:
                story.append(Paragraph("✅ No threats detected in this period.", self.body_style))

            # Footer
            story.append(Spacer(1, 0.3 * inch))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f3460")))
            story.append(Spacer(1, 0.1 * inch))
            story.append(
                Paragraph(
                    "Generated by RansomGuard v1.0.0 | Machine Learning Based Ransomware Detection",
                    ParagraphStyle(
                        "Footer",
                        parent=self.styles["Normal"],
                        fontSize=7,
                        textColor=colors.grey,
                        alignment=TA_CENTER,
                    ),
                )
            )

            doc.build(story)
            logger.info(f"PDF report generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return False