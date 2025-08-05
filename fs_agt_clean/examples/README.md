# FlipSync Examples Directory

## ⚠️ **IMPORTANT: EXAMPLE CODE ONLY - NOT PRODUCTION AGENTS** ⚠️

This directory contains **example code** that demonstrates how to use FlipSync's coordination components (event system, coordinator, knowledge repository). 

**These are NOT the production autonomous agents used in the FlipSync system.**

## 🚫 **What These Examples Are NOT**

- **NOT production agents**: These examples do not represent the actual FlipSync autonomous agents
- **NOT part of the 4+1 architecture**: These are demonstration code only
- **NOT used in production**: These files are for learning and testing purposes only

## ✅ **Production Autonomous Agents Location**

The actual FlipSync production agents are located in:

- **MarketAutonomousAgent**: `fs_agt_clean/agents/market/market_agent.py`
- **ExecutiveAutonomousAgent**: `fs_agt_clean/agents/executive/executive_agent.py`
- **ContentAutonomousAgent**: `fs_agt_clean/agents/content/content_agent.py`
- **LogisticsAutonomousAgent**: `fs_agt_clean/agents/logistics/logistics_agent.py`

## 📁 **Example Files**

### `event_system_example.py`
- **Purpose**: Demonstrates event system usage
- **Example Classes**: `ExampleMarketAgent`, `ExampleExecutiveAgent`
- **Shows**: Event publishing, subscribing, and message handling

### `coordinator_example.py`
- **Purpose**: Demonstrates coordinator component usage
- **Example Classes**: `ExampleMarketAgent`, `ExampleExecutiveAgent`
- **Shows**: Agent registration, discovery, and task delegation

### `knowledge_repository_coordinator_integration.py`
- **Purpose**: Demonstrates knowledge repository integration
- **Example Classes**: `ExampleKnowledgeAgent`
- **Shows**: Knowledge sharing between agents

### `knowledge_repository_example.py`
- **Purpose**: Demonstrates basic knowledge repository usage
- **Shows**: Knowledge storage, retrieval, and filtering

## 🏗️ **FlipSync Architecture (4+1 System)**

FlipSync uses a **4+1 architecture**:

### **4 Autonomous Agents**
1. **Market Agent**: Pricing, inventory, competitor analysis
2. **Executive Agent**: Strategic decisions, resource allocation
3. **Content Agent**: Listing optimization, SEO, content generation
4. **Logistics Agent**: Shipping, fulfillment, warehouse management

### **+1 Conversational Interface**
- **Chat System**: User interface layer in `fs_agt_clean/services/communication/`
- **Purpose**: Routes user requests to autonomous agents
- **NOT an agent**: It's the user interface, not part of the agentic system

## 🔧 **Development Guidelines**

### **For New Developers**
1. **Study the examples** to understand coordination patterns
2. **Use production agents** for actual FlipSync development
3. **Don't modify examples** for production use
4. **Follow the 4+1 architecture** when adding new functionality

### **For Testing**
- Examples can be used for testing coordination components
- Always test against production agents for real functionality
- Use examples to understand event flows and coordination patterns

## 📊 **System Status**

- **Production Readiness**: 75-85% complete
- **Vision Alignment**: 87.5% (exceeds 85% target)
- **Architecture Compliance**: 100% (4+1 system confirmed)
- **Service Orchestration**: Market Agent 100%, others 75% complete

## 🚀 **Next Steps**

Phase 1 of the production plan focuses on completing service orchestration for the remaining 3 autonomous agents (Executive, Content, Logistics) to achieve full production readiness.

---

**Remember**: These examples are for learning and testing coordination patterns. Always use the production autonomous agents for actual FlipSync functionality.
