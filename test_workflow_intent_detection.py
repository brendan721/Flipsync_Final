#!/usr/bin/env python3
"""
Test script for workflow intent detection system.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/app')

from fs_agt_clean.core.workflow_intent_detector import workflow_intent_detector

def test_workflow_intent_detection():
    """Test workflow intent detection with various messages."""
    print("🎯 Testing Workflow Intent Detection System")
    print("=" * 60)
    
    # Test messages for different workflow types
    test_messages = [
        # Product Analysis Workflow
        "Can you analyze this product for me? It's a MacBook Pro M3",
        "I want to evaluate this item to see if it's worth selling",
        "Should I sell this iPhone 15 Pro on eBay?",
        "What do you think about this product's market potential?",
        
        # Listing Optimization Workflow
        "Can you help me optimize my listing for better SEO?",
        "I need to improve my product listing on Amazon",
        "How can I make my listing perform better?",
        "Please optimize my listing keywords and title",
        
        # Decision Consensus Workflow
        "I need help deciding whether to buy this inventory",
        "What do you think I should do about pricing?",
        "Can you help me make a decision about this strategy?",
        "I need advice from multiple agents on this",
        
        # Pricing Strategy Workflow
        "I need help with pricing strategy for my products",
        "Can you do a competitive pricing analysis?",
        "What price should I charge for this item?",
        "Help me with pricing optimization",
        
        # Market Research Workflow
        "I need market research for electronics category",
        "Can you analyze the competitive landscape?",
        "What are the market trends for this product type?",
        "I want comprehensive market analysis",
        
        # Non-workflow messages (should not trigger workflows)
        "Hello, how are you?",
        "What's the weather like?",
        "Can you help me with shipping?",
        "I have a question about my account",
    ]
    
    workflow_detected_count = 0
    total_messages = len(test_messages)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}/{total_messages}: '{message}'")
        print("-" * 50)
        
        # Detect workflow intent
        workflow_intent = workflow_intent_detector.detect_workflow_intent(message)
        
        if workflow_intent:
            workflow_detected_count += 1
            print(f"✅ WORKFLOW DETECTED:")
            print(f"   🎯 Type: {workflow_intent.workflow_type}")
            print(f"   📊 Confidence: {workflow_intent.confidence:.2f}")
            print(f"   👥 Agents: {', '.join(workflow_intent.participating_agents)}")
            print(f"   🔍 Trigger phrases: {', '.join(workflow_intent.trigger_phrases[:3])}...")
            print(f"   📋 Context: {workflow_intent.context}")
        else:
            print(f"❌ No workflow detected - will route to single agent")
    
    print("\n" + "=" * 60)
    print("📊 WORKFLOW INTENT DETECTION SUMMARY")
    print("=" * 60)
    print(f"✅ Total messages tested: {total_messages}")
    print(f"🎯 Workflows detected: {workflow_detected_count}")
    print(f"📈 Detection rate: {workflow_detected_count/total_messages*100:.1f}%")
    
    # Test supported workflows
    print(f"\n🔧 Supported workflow types:")
    for workflow_type in workflow_intent_detector.get_supported_workflows():
        description = workflow_intent_detector.get_workflow_description(workflow_type)
        print(f"   • {workflow_type}: {description['description']}")
    
    print(f"\n🎉 Workflow intent detection system is ready!")

if __name__ == "__main__":
    test_workflow_intent_detection()
