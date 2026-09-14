import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from database.connection import get_collection
from services.threat_service import ThreatService
from services.system_service import SystemService
from utils.pdf_generator import PDFReportGenerator
from utils.logger import setup_logger
from utils.helpers import generate_id

logger = setup_logger("report_service", "logs/reports.log")

REPORTS_DIR = "reports"


class ReportService:
    """Service for generating and managing reports."""

    def __init__(self):
        self.threat_service = ThreatService()
        self.system_service = SystemService()
        self.pdf_generator = PDFReportGenerator()
        os.makedirs(REPORTS_DIR, exist_ok=True)

    async def generate_report(
        self,
        report_type: str,
        format: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_system_info: bool = True,
        include_threats: bool = True,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a report in the specified format.

        Args:
            report_type: Type of report
            format: Output format (pdf/csv/json)
            start_date: Start date filter
            end_date: End date filter
            include_system_info: Include system information
            include_threats: Include threat data
            title: Report title

        Returns:
            Report metadata dictionary
        """
        try:
            report_id = generate_id()
            timestamp = datetime.utcnow()
            title = title or f"RansomGuard {report_type.replace('_', ' ').title()} Report"

            # Fetch data
            threats_data = []
            if include_threats:
                result = await self.threat_service.get_threats(
                    limit=1000,
                    start_date=start_date,
                    end_date=end_date,
                )
                threats_data = result.get("threats", [])

            system_info = None
            if include_system_info:
                system_info = self.system_service.get_system_info()

            # Generate based on format
            if format == "pdf":
                file_path, file_name = await self._generate_pdf(
                    report_id, title, threats_data, system_info, start_date, end_date
                )
            elif format == "csv":
                file_path, file_name = await self._generate_csv(
                    report_id, title, threats_data
                )
            elif format == "json":
                file_path, file_name = await self._generate_json(
                    report_id, title, threats_data, system_info
                )
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            # Store report metadata
            report_meta = {
                "report_id": report_id,
                "title": title,
                "report_type": report_type,
                "format": format,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "created_at": timestamp,
                "start_date": start_date,
                "end_date": end_date,
                "threat_count": len(threats_data),
                "generated_by": "RansomGuard System",
            }

            await self._save_report_metadata(report_meta)

            return report_meta

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    async def _generate_pdf(
        self,
        report_id: str,
        title: str,
        threats: List[Dict],
        system_info: Optional[Dict],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ):
        """Generate PDF report."""
        file_name = f"report_{report_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(REPORTS_DIR, file_name)

        # Format system info for PDF
        sys_info_formatted = None
        if system_info:
            sys_info_formatted = {
                "hostname": system_info.get("hostname", "N/A"),
                "platform": system_info.get("platform", "N/A"),
                "architecture": system_info.get("architecture", "N/A"),
                "cpu_percent": system_info.get("cpu", {}).get("percent", "N/A"),
                "memory_percent": system_info.get("memory", {}).get("percent", "N/A"),
                "uptime": f"{system_info.get('uptime_seconds', 0) / 3600:.1f} hours",
            }

        success = self.pdf_generator.generate_threat_report(
            output_path=file_path,
            threats=threats,
            system_info=sys_info_formatted,
            start_date=start_date,
            end_date=end_date,
            title=title,
        )

        if not success:
            raise RuntimeError("PDF generation failed")

        return file_path, file_name

    async def _generate_csv(self, report_id: str, title: str, threats: List[Dict]):
        """Generate CSV report."""
        file_name = f"report_{report_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(REPORTS_DIR, file_name)

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            if not threats:
                csvfile.write("No threats found\n")
                return file_path, file_name

            fieldnames = [
                "threat_id", "file_name", "file_path", "file_extension",
                "threat_level", "confidence", "risk_score", "is_ransomware",
                "status", "process_name", "process_id", "event_type",
                "recommended_action", "action_taken", "timestamp",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for threat in threats:
                row = {field: threat.get(field, "") for field in fieldnames}
                # Format datetime objects
                if isinstance(row.get("timestamp"), datetime):
                    row["timestamp"] = row["timestamp"].isoformat()
                writer.writerow(row)

        return file_path, file_name

    async def _generate_json(
        self, report_id: str, title: str, threats: List[Dict], system_info: Optional[Dict]
    ):
        """Generate JSON report."""
        file_name = f"report_{report_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(REPORTS_DIR, file_name)

        report_data = {
            "report_id": report_id,
            "title": title,
            "generated_at": datetime.utcnow().isoformat(),
            "system_info": system_info,
            "threat_count": len(threats),
            "threats": [],
        }

        for threat in threats:
            # Convert datetime objects to strings
            serializable_threat = {}
            for key, value in threat.items():
                if isinstance(value, datetime):
                    serializable_threat[key] = value.isoformat()
                else:
                    serializable_threat[key] = value
            report_data["threats"].append(serializable_threat)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        return file_path, file_name

    async def _save_report_metadata(self, report_meta: Dict):
        """Save report metadata to database."""
        try:
            collection = get_collection("reports")
            await collection.insert_one(report_meta)
        except Exception as e:
            logger.error(f"Error saving report metadata: {e}")

    async def get_reports(self, limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        """Get list of generated reports."""
        try:
            collection = get_collection("reports")
            total = await collection.count_documents({})
            cursor = collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
            reports = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                if isinstance(doc.get("created_at"), datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
                if isinstance(doc.get("start_date"), datetime):
                    doc["start_date"] = doc["start_date"].isoformat()
                if isinstance(doc.get("end_date"), datetime):
                    doc["end_date"] = doc["end_date"].isoformat()
                reports.append(doc)

            return {"total": total, "reports": reports}
        except Exception as e:
            logger.error(f"Error getting reports: {e}")
            raise


def get_report_service() -> ReportService:
    return ReportService()