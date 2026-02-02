"""
MuBot Basic Usage Examples

This file demonstrates common use cases for MuBot.
Copy and modify these examples for your own job search.
"""

import asyncio
from datetime import datetime, timedelta

from mubot.agent import JobSearchAgent
from memory.models import OutreachEntry, OutreachStatus
from mubot.pipelines import JobPipeline, PipelineStage


async def example_1_draft_and_send():
    """Example 1: Draft a cold email and send it."""
    
    print("=" * 60)
    print("Example 1: Draft and Send a Cold Email")
    print("=" * 60)
    
    # Initialize the agent
    agent = JobSearchAgent()
    initialized = await agent.initialize()
    
    if not initialized:
        print("❌ Failed to initialize. Run 'mubot-init' first.")
        return
    
    # Draft an email
    draft, warnings = await agent.draft_email(
        company_name="Example Corp",
        role_title="Senior Software Engineer",
        company_context="Fast-growing fintech startup, recently raised Series B",
        job_description="Looking for experienced backend engineer to build payment systems",
        recipient_name="Sarah Johnson",
        recipient_email="sarah.johnson@example.com",
        recipient_title="Engineering Manager",
    )
    
    print(f"\n📧 Draft Created:")
    print(f"Subject: {draft.subject}")
    print(f"\n{draft.body}")
    
    if warnings:
        print("\n⚠️ Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # In real usage, you would review and approve:
    # user_approved = input("\nSend this email? (yes/no): ").lower() == "yes"
    
    # For demo, we'll skip actual sending
    print("\n💡 In production, you would approve and send:")
    print("   success, message = await agent.send_email(draft, approved=True)")


async def example_2_schedule_followup():
    """Example 2: Schedule a follow-up email."""
    
    print("\n" + "=" * 60)
    print("Example 2: Schedule a Follow-Up")
    print("=" * 60)
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    # Create a sample entry (in real usage, this would be loaded from memory)
    entry = OutreachEntry(
        id="sample-123",
        recipient_email="hiring@company.com",
        recipient_name="Hiring Manager",
        company_name="Tech Startup",
        role_title="Full Stack Engineer",
        subject="Interest in Full Stack Role",
        body="Sample email body...",
        status=OutreachStatus.SENT,
        sent_at=datetime.utcnow() - timedelta(days=5),
        followup_count=0,
    )
    
    # Schedule follow-up in 3 days
    success, message = await agent.schedule_followup(entry, days_delay=3)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")


async def example_3_track_pipeline():
    """Example 3: Track opportunities in pipeline."""
    
    print("\n" + "=" * 60)
    print("Example 3: Job Pipeline Tracking")
    print("=" * 60)
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    # Create pipeline manager
    from mubot.memory import MemoryManager
    pipeline = JobPipeline(agent.memory)
    
    # Add opportunities
    opp1 = pipeline.add_opportunity(
        company_name="Stripe",
        role_title="Staff Engineer",
        job_url="https://stripe.com/jobs/123",
        salary_range="$200k-$280k",
        notes="Dream company, fintech experience matches well",
    )
    
    opp2 = pipeline.add_opportunity(
        company_name="OpenAI",
        role_title="Research Engineer",
        job_url="https://openai.com/jobs/456",
        notes="AI/ML focus, interesting challenges",
    )
    
    print(f"✅ Added {opp1.company_name} - {opp1.role_title}")
    print(f"✅ Added {opp2.company_name} - {opp2.role_title}")
    
    # Advance stages
    pipeline.advance_stage(opp1.id, PipelineStage.CONTACTED, "Sent cold email to hiring manager")
    pipeline.advance_stage(opp2.id, PipelineStage.APPLIED, "Applied through careers page")
    
    # Get summary
    print("\n📊 Pipeline Summary:")
    print(pipeline.get_pipeline_summary())


async def example_4_search_memory():
    """Example 4: Search past outreach for insights."""
    
    print("\n" + "=" * 60)
    print("Example 4: Search Memory with RAG")
    print("=" * 60)
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    from mubot.tools import RAGEngine
    from mubot.config import get_settings
    
    settings = get_settings()
    rag = RAGEngine(settings)
    
    initialized = await rag.initialize()
    if not initialized:
        print("❌ Failed to initialize RAG engine")
        return
    
    print(f"✅ RAG engine initialized with {rag.get_stats()['total_documents']} documents")
    
    # Search for successful templates
    print("\n🔍 Searching for successful fintech outreach templates...")
    results = await rag.get_successful_templates(role_type="fintech")
    
    print(f"Found {len(results)} templates")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. Similarity: {result['similarity']:.2f}")
        print(f"   Company: {result['metadata'].get('company', 'Unknown')}")


async def example_5_daily_summary():
    """Example 5: Generate daily summary."""
    
    print("\n" + "=" * 60)
    print("Example 5: Daily Summary")
    print("=" * 60)
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    # Get daily stats
    stats = agent.memory.get_daily_stats()
    
    print(f"\n📅 Today's Activity ({stats.date}):")
    print(f"   Emails sent: {stats.emails_sent}")
    print(f"   Replies received: {stats.replies_received}")
    print(f"   Positive responses: {stats.positive_responses}")
    print(f"   Daily limit: {stats.emails_sent}/{agent.settings.max_daily_emails}")
    
    # Generate LLM summary
    print("\n📝 Generating detailed summary...")
    summary = await agent.get_daily_summary()
    print(summary)


async def main():
    """Run all examples."""
    
    print("\n" + "🤖 " * 20)
    print("MuBot Usage Examples")
    print("🤖 " * 20 + "\n")
    
    try:
        await example_1_draft_and_send()
        await example_2_schedule_followup()
        await example_3_track_pipeline()
        await example_4_search_memory()
        await example_5_daily_summary()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
