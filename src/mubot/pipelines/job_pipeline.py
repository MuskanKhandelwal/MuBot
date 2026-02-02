"""
Job Pipeline Tracker

This module provides comprehensive tracking of job opportunities through
the various stages of a job search. It maintains:
- Job details (company, role, description)
- Pipeline stage progression
- Associated outreach emails
- Next actions and reminders
- Outcome tracking

The pipeline integrates with Notion (optional) for visualization and
provides both programmatic and human-readable views of progress.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from mubot.memory.models import JobOpportunity, OutreachEntry
from mubot.memory.persistence import JsonStore


class PipelineStage(str, Enum):
    """Standard stages in a job search pipeline."""
    IDENTIFIED = "identified"           # Found interesting role
    RESEARCHED = "researched"           # Gathered company info
    CONTACTED = "contacted"             # Sent cold email
    APPLIED = "applied"                 # Formal application submitted
    REPLIED = "replied"                 # Received response
    PHONE_SCREEN = "phone_screen"       # Phone/video screen scheduled
    INTERVIEW = "interview"             # In interview process
    FINAL_ROUND = "final_round"         # Final interviews
    OFFER = "offer"                     # Received offer
    NEGOTIATING = "negotiating"         # Negotiating terms
    ACCEPTED = "accepted"               # Accepted offer
    REJECTED = "rejected"               # Rejected by company
    DECLINED = "declined"               # Declined offer
    WITHDRAWN = "withdrawn"             # Withdrew application


class JobPipeline:
    """
    Manages the job search pipeline.
    
    This class provides methods to:
    - Add new job opportunities
    - Track stage progression
    - Associate outreach emails with opportunities
    - Generate pipeline reports
    - Export to external systems (Notion, etc.)
    
    Usage:
        pipeline = JobPipeline(memory_manager)
        
        # Add opportunity
        opp = pipeline.add_opportunity(
            company_name="TechCorp",
            role_title="Senior Engineer",
            job_url="https://...",
        )
        
        # Advance stage
        pipeline.advance_stage(opp.id, PipelineStage.CONTACTED)
        
        # Get funnel stats
        stats = pipeline.get_funnel_stats()
    """
    
    # Stage definitions with descriptions
    STAGE_DEFINITIONS = {
        PipelineStage.IDENTIFIED: {
            "description": "Role identified, initial interest",
            "action": "Research company and role",
        },
        PipelineStage.RESEARCHED: {
            "description": "Company research complete",
            "action": "Draft personalized outreach",
        },
        PipelineStage.CONTACTED: {
            "description": "Cold email sent",
            "action": "Wait for response, prepare follow-up",
        },
        PipelineStage.APPLIED: {
            "description": "Formal application submitted",
            "action": "Track application status",
        },
        PipelineStage.REPLIED: {
            "description": "Received response from company",
            "action": "Respond promptly, schedule next steps",
        },
        PipelineStage.PHONE_SCREEN: {
            "description": "Phone/video screen scheduled",
            "action": "Prepare for screening call",
        },
        PipelineStage.INTERVIEW: {
            "description": "In interview process",
            "action": "Prepare for interviews, send thank you notes",
        },
        PipelineStage.FINAL_ROUND: {
            "description": "Final round interviews",
            "action": "Final preparation, references ready",
        },
        PipelineStage.OFFER: {
            "description": "Offer received",
            "action": "Evaluate offer, prepare negotiation",
        },
        PipelineStage.NEGOTIATING: {
            "description": "Negotiating terms",
            "action": "Finalize negotiation details",
        },
        PipelineStage.ACCEPTED: {
            "description": "Offer accepted",
            "action": "Celebrate and prepare for new role",
        },
        PipelineStage.REJECTED: {
            "description": "Rejected by company",
            "action": "Request feedback, update records",
        },
        PipelineStage.DECLINED: {
            "description": "Declined offer",
            "action": "Maintain relationship, document learnings",
        },
        PipelineStage.WITHDRAWN: {
            "description": "Withdrew application",
            "action": "Document reason, maintain relationship",
        },
    }
    
    def __init__(self, memory_manager=None, storage_path: str = "./data"):
        """
        Initialize the job pipeline.
        
        Args:
            memory_manager: MemoryManager for persistence
            storage_path: Path for local storage
        """
        self.memory = memory_manager
        self.storage = JsonStore(storage_path)
        self._opportunities: dict[str, JobOpportunity] = {}
        self._load_opportunities()
    
    def _load_opportunities(self):
        """Load opportunities from persistent storage."""
        data = self.storage.read_json("pipelines/opportunities.json")
        if data:
            for opp_id, opp_data in data.items():
                try:
                    self._opportunities[opp_id] = JobOpportunity.model_validate(opp_data)
                except Exception as e:
                    print(f"Error loading opportunity {opp_id}: {e}")
    
    def _save_opportunities(self):
        """Save opportunities to persistent storage."""
        data = {
            opp_id: opp.model_dump() 
            for opp_id, opp in self._opportunities.items()
        }
        self.storage.write_json("pipelines/opportunities.json", data)
    
    # ======================================================================
    # CRUD Operations
    # ======================================================================
    
    def add_opportunity(
        self,
        company_name: str,
        role_title: str,
        job_description: Optional[str] = None,
        job_url: Optional[str] = None,
        salary_range: Optional[str] = None,
        location: Optional[str] = None,
        is_remote: Optional[bool] = None,
        notes: Optional[str] = None,
    ) -> JobOpportunity:
        """
        Add a new job opportunity to the pipeline.
        
        Args:
            company_name: Company name
            role_title: Job title
            job_description: Full job description
            job_url: Link to job posting
            salary_range: Listed salary range
            location: Job location
            is_remote: Whether remote is allowed
            notes: Initial notes
        
        Returns:
            Created JobOpportunity
        """
        opp = JobOpportunity(
            id=str(uuid.uuid4()),
            company_name=company_name,
            role_title=role_title,
            job_description=job_description,
            job_url=job_url,
            salary_range=salary_range,
            location=location,
            is_remote=is_remote,
            stage=PipelineStage.IDENTIFIED.value,
        )
        
        if notes:
            opp.notes.append({
                "date": datetime.utcnow().isoformat(),
                "content": notes,
            })
        
        self._opportunities[opp.id] = opp
        self._save_opportunities()
        
        return opp
    
    def get_opportunity(self, opp_id: str) -> Optional[JobOpportunity]:
        """
        Get an opportunity by ID.
        
        Args:
            opp_id: Opportunity ID
        
        Returns:
            JobOpportunity if found, None otherwise
        """
        return self._opportunities.get(opp_id)
    
    def update_opportunity(
        self,
        opp_id: str,
        **kwargs,
    ) -> Optional[JobOpportunity]:
        """
        Update an opportunity's fields.
        
        Args:
            opp_id: Opportunity ID
            **kwargs: Fields to update
        
        Returns:
            Updated JobOpportunity if found
        """
        opp = self._opportunities.get(opp_id)
        if not opp:
            return None
        
        for key, value in kwargs.items():
            if hasattr(opp, key):
                setattr(opp, key, value)
        
        opp.updated_at = datetime.utcnow()
        self._save_opportunities()
        
        return opp
    
    def delete_opportunity(self, opp_id: str) -> bool:
        """
        Delete an opportunity.
        
        Args:
            opp_id: Opportunity ID
        
        Returns:
            True if deleted
        """
        if opp_id in self._opportunities:
            del self._opportunities[opp_id]
            self._save_opportunities()
            return True
        return False
    
    # ======================================================================
    # Stage Management
    # ======================================================================
    
    def advance_stage(
        self,
        opp_id: str,
        new_stage: PipelineStage,
        notes: Optional[str] = None,
    ) -> Optional[JobOpportunity]:
        """
        Advance an opportunity to a new stage.
        
        Args:
            opp_id: Opportunity ID
            new_stage: Target stage
            notes: Optional notes about the transition
        
        Returns:
            Updated JobOpportunity if found
        """
        opp = self._opportunities.get(opp_id)
        if not opp:
            return None
        
        old_stage = opp.stage
        opp.stage = new_stage.value
        
        # Add transition note
        note_content = f"Stage changed: {old_stage} → {new_stage.value}"
        if notes:
            note_content += f" | {notes}"
        
        opp.notes.append({
            "date": datetime.utcnow().isoformat(),
            "content": note_content,
        })
        
        # Update next action based on stage
        stage_info = self.STAGE_DEFINITIONS.get(new_stage, {})
        opp.next_action = stage_info.get("action")
        
        self._save_opportunities()
        
        return opp
    
    def get_stage_description(self, stage: PipelineStage) -> dict:
        """
        Get description and recommended action for a stage.
        
        Args:
            stage: Pipeline stage
        
        Returns:
            Dict with description and action
        """
        return self.STAGE_DEFINITIONS.get(stage, {
            "description": "Unknown stage",
            "action": "Review pipeline",
        })
    
    # ======================================================================
    # Outreach Association
    # ======================================================================
    
    def link_outreach(
        self,
        opp_id: str,
        outreach_entry: OutreachEntry,
    ) -> bool:
        """
        Link an outreach email to an opportunity.
        
        Args:
            opp_id: Opportunity ID
            outreach_entry: Outreach entry to link
        
        Returns:
            True if linked successfully
        """
        opp = self._opportunities.get(opp_id)
        if not opp:
            return False
        
        opp.outreach_entry_ids.append(outreach_entry.id)
        
        # Update stage if appropriate
        if opp.stage == PipelineStage.RESEARCHED.value:
            self.advance_stage(opp_id, PipelineStage.CONTACTED)
        
        self._save_opportunities()
        return True
    
    # ======================================================================
    # Queries and Reports
    # ======================================================================
    
    def get_active_opportunities(
        self,
        stage: Optional[PipelineStage] = None,
    ) -> list[JobOpportunity]:
        """
        Get all active (non-closed) opportunities.
        
        Args:
            stage: Optional stage filter
        
        Returns:
            List of active opportunities
        """
        closed_stages = {
            PipelineStage.ACCEPTED.value,
            PipelineStage.REJECTED.value,
            PipelineStage.DECLINED.value,
            PipelineStage.WITHDRAWN.value,
        }
        
        results = []
        for opp in self._opportunities.values():
            if opp.stage not in closed_stages:
                if stage is None or opp.stage == stage.value:
                    results.append(opp)
        
        return results
    
    def get_funnel_stats(self) -> dict:
        """
        Get pipeline funnel statistics.
        
        Returns:
            Dict with counts at each stage
        """
        stats = {stage.value: 0 for stage in PipelineStage}
        
        for opp in self._opportunities.values():
            if opp.stage in stats:
                stats[opp.stage] += 1
        
        # Calculate conversion rates
        total = len(self._opportunities)
        active = len([o for o in self._opportunities.values() if o.is_active])
        
        return {
            "by_stage": stats,
            "total_opportunities": total,
            "active": active,
            "closed": total - active,
        }
    
    def get_pipeline_summary(self) -> str:
        """
        Generate a human-readable pipeline summary.
        
        Returns:
            Formatted summary string
        """
        stats = self.get_funnel_stats()
        active = self.get_active_opportunities()
        
        lines = [
            "=" * 60,
            "📊 Job Pipeline Summary",
            "=" * 60,
            "",
            f"Total Opportunities: {stats['total_opportunities']}",
            f"Active: {stats['active']} | Closed: {stats['closed']}",
            "",
            "Stage Breakdown:",
        ]
        
        for stage in [
            PipelineStage.IDENTIFIED,
            PipelineStage.CONTACTED,
            PipelineStage.REPLIED,
            PipelineStage.INTERVIEW,
            PipelineStage.OFFER,
        ]:
            count = stats["by_stage"][stage.value]
            lines.append(f"  {stage.value}: {count}")
        
        if active:
            lines.extend([
                "",
                "Active Opportunities:",
            ])
            for opp in active[:10]:  # Limit to 10
                lines.append(f"  • {opp.company_name} - {opp.role_title} ({opp.stage})")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    # ======================================================================
    # Notion Integration (Optional)
    # ======================================================================
    
    async def sync_to_notion(self, notion_client=None) -> bool:
        """
        Sync opportunities to Notion database.
        
        Args:
            notion_client: Notion client instance
        
        Returns:
            True if sync successful
        """
        # TODO: Implement Notion sync
        print("Notion sync not yet implemented")
        return False
