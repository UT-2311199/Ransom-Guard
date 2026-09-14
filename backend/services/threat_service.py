from datetime import datetime
from typing import Dict, Any, List, Optional

from bson import ObjectId

from database.connection import get_collection
from utils.logger import setup_logger

logger = setup_logger("threat_service", "logs/threats.log")


class ThreatService:
    """Service for managing threat logs and analytics."""

    async def get_threats(
        self,
        limit: int = 100,
        skip: int = 0,
        status: Optional[str] = None,
        threat_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve threat logs with optional filters.

        Args:
            limit: Maximum records to return
            skip: Records to skip for pagination
            status: Filter by status
            threat_level: Filter by threat level
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Threats data dictionary
        """
        try:
            collection = get_collection("threat_logs")

            # Build query
            query = {}
            if status:
                query["status"] = status
            if threat_level:
                query["threat_level"] = threat_level
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date

            # Count total
            total = await collection.count_documents(query)

            # Fetch records
            cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            threats = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                threats.append(doc)

            return {
                "total": total,
                "skip": skip,
                "limit": limit,
                "threats": threats,
            }

        except Exception as e:
            logger.error(f"Error getting threats: {e}")
            raise

    async def get_threat_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of all threats.

        Returns:
            Summary dictionary
        """
        try:
            collection = get_collection("threat_logs")

            total = await collection.count_documents({})
            active = await collection.count_documents({"status": "active"})
            resolved = await collection.count_documents({"status": "resolved"})
            quarantined = await collection.count_documents({"status": "quarantined"})
            critical = await collection.count_documents({"threat_level": "critical"})
            high = await collection.count_documents({"threat_level": "high"})
            medium = await collection.count_documents({"threat_level": "medium"})
            low = await collection.count_documents({"threat_level": "low"})
            safe = await collection.count_documents({"threat_level": "safe"})
            ransomware = await collection.count_documents({"is_ransomware": True})

            # Get last threat timestamp
            last_threat_cursor = collection.find({"status": "active"}).sort("timestamp", -1).limit(1)
            last_threat = None
            async for doc in last_threat_cursor:
                last_threat = doc.get("timestamp")

            return {
                "total_threats": total,
                "active_threats": active,
                "resolved_threats": resolved,
                "quarantined_count": quarantined,
                "critical_count": critical,
                "high_count": high,
                "medium_count": medium,
                "low_count": low,
                "safe_count": safe,
                "ransomware_detected": ransomware,
                "last_threat_at": last_threat.isoformat() if last_threat else None,
            }

        except Exception as e:
            logger.error(f"Error getting threat summary: {e}")
            raise

    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get detailed analytics data for dashboard.

        Returns:
            Analytics data dictionary
        """
        try:
            collection = get_collection("threat_logs")

            # Threats by level
            level_pipeline = [
                {"$group": {"_id": "$threat_level", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
            level_cursor = collection.aggregate(level_pipeline)
            threats_by_level = {}
            async for doc in level_cursor:
                threats_by_level[doc["_id"]] = doc["count"]

            # Threats by day (last 30 days)
            daily_pipeline = [
                {
                    "$match": {
                        "timestamp": {
                            "$gte": datetime.utcnow().replace(
                                hour=0, minute=0, second=0
                            ).__class__(
                                datetime.utcnow().year,
                                datetime.utcnow().month,
                                1,
                            )
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                            }
                        },
                        "count": {"$sum": 1},
                        "ransomware_count": {
                            "$sum": {"$cond": [{"$eq": ["$is_ransomware", True]}, 1, 0]}
                        },
                    }
                },
                {"$sort": {"_id": 1}},
            ]
            daily_cursor = collection.aggregate(daily_pipeline)
            threats_by_day = []
            async for doc in daily_cursor:
                threats_by_day.append(
                    {
                        "date": doc["_id"],
                        "count": doc["count"],
                        "ransomware": doc["ransomware_count"],
                    }
                )

            # Top targeted extensions
            ext_pipeline = [
                {"$match": {"file_extension": {"$exists": True, "$ne": None, "$ne": ""}}},
                {"$group": {"_id": "$file_extension", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            ext_cursor = collection.aggregate(ext_pipeline)
            top_extensions = []
            async for doc in ext_cursor:
                top_extensions.append({"extension": doc["_id"], "count": doc["count"]})

            # Top processes
            proc_pipeline = [
                {"$match": {"process_name": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$process_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            proc_cursor = collection.aggregate(proc_pipeline)
            top_processes = []
            async for doc in proc_cursor:
                top_processes.append({"process": doc["_id"], "count": doc["count"]})

            # Status distribution
            status_pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            ]
            status_cursor = collection.aggregate(status_pipeline)
            status_distribution = {}
            async for doc in status_cursor:
                status_distribution[doc["_id"]] = doc["count"]

            summary = await self.get_threat_summary()

            return {
                "summary": summary,
                "threats_by_level": threats_by_level,
                "threats_by_day": threats_by_day,
                "top_targeted_extensions": top_extensions,
                "top_suspicious_processes": top_processes,
                "status_distribution": status_distribution,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            raise

    async def update_threat_status(
        self, threat_id: str, status: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of a threat record."""
        try:
            collection = get_collection("threat_logs")
            update_data = {
                "status": status,
                "resolved_at": datetime.utcnow() if status == "resolved" else None,
            }
            if notes:
                update_data["notes"] = notes

            result = await collection.update_one(
                {"threat_id": threat_id},
                {"$set": update_data},
            )

            if result.matched_count == 0:
                return {"success": False, "error": "Threat not found"}

            return {
                "success": True,
                "threat_id": threat_id,
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error updating threat status: {e}")
            raise


def get_threat_service() -> ThreatService:
    return ThreatService()