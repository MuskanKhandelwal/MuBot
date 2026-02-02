# =============================================================================
# Pipelines Package
# =============================================================================
# This package handles job application pipeline tracking and management.
# 
# A job search pipeline typically moves through stages:
#   1. Identified → Found interesting role/company
#   2. Researched → Gathered information, prepared outreach
#   3. Contacted → Sent cold email or applied
#   4. Replied → Received response
#   5. Interview → In interview process
#   6. Offer → Received offer
#   7. Rejected → Not moving forward
#
# The pipeline tracker maintains this state and provides visibility
# into the overall job search progress.
# =============================================================================

from mubot.pipelines.job_pipeline import JobPipeline, PipelineStage

__all__ = [
    "JobPipeline",
    "PipelineStage",
]
