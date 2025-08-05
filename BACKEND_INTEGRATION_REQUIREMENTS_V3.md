# Backend Integration Requirements for FlipSync V3
## New API Endpoints and Enhancements Needed

**Document Purpose**: Define specific backend API requirements for V3 implementation  
**Target**: FastAPI backend integration points for adaptive Flutter frontend  
**Priority**: Critical path items for V3 roadmap success

---

## 🎯 **CRITICAL NEW ENDPOINTS REQUIRED**

### **1. User Profile & Inventory Source Preferences**
```python
# /api/v1/users/profile
GET    /api/v1/users/profile                    # Get user profile with inventory source
PUT    /api/v1/users/profile                    # Update user profile
POST   /api/v1/users/preferences                # Set inventory source preference
GET    /api/v1/users/preferences                # Get user preferences

# Request/Response Models
class UserProfile:
    user_id: str
    inventory_source: str  # 'liquidation', 'thrifting', 'miscellaneous'
    selling_style: str     # 'aggressive', 'balanced', 'conservative'
    inventory_size: str    # 'small', 'medium', 'large'
    ebay_location: str     # For shipping zone calculations
    preferences: Dict[str, Any]
```

### **2. Adaptive Opportunity System**
```python
# /api/v1/opportunities/
GET    /api/v1/opportunities/trending/{source}           # Source-specific trending items
GET    /api/v1/opportunities/liquidation                 # BIDFTA/A-Stock opportunities
GET    /api/v1/opportunities/thrifting                   # Brand recognition alerts
GET    /api/v1/opportunities/miscellaneous               # General market opportunities
POST   /api/v1/opportunities/alert                       # Set opportunity alerts

# Response Models
class OpportunityResponse:
    opportunities: List[Opportunity]
    source_type: str
    last_updated: datetime
    
class Opportunity:
    item_name: str
    trend_type: str        # 'trending', 'seasonal', 'brand_alert'
    market_data: Dict[str, Any]
    profit_potential: str
    risk_level: str
    action_items: List[str]
```

### **3. Physical Assessment Workflow**
```python
# /api/v1/assessment/
POST   /api/v1/assessment/start                          # Start assessment workflow
PUT    /api/v1/assessment/{assessment_id}/photos         # Upload photos
PUT    /api/v1/assessment/{assessment_id}/condition      # Update condition
PUT    /api/v1/assessment/{assessment_id}/completeness   # Update completeness
POST   /api/v1/assessment/{assessment_id}/complete       # Complete assessment

# Enhanced product specifications
GET    /api/v1/products/specifications/{product_id}      # Dynamic completeness checklist
POST   /api/v1/products/identify                         # AI product identification
```

### **4. Shipping Arbitrage System (CRITICAL REVENUE SOURCE)**
```python
# /api/v1/shipping/
GET    /api/v1/shipping/zones/{seller_zip}               # USPS zones from seller location
POST   /api/v1/shipping/arbitrage                        # FlipSync vs eBay shipping comparison
POST   /api/v1/shipping/shippo/poly                      # Dimensional shipping via Shippo (2 dimensions)
POST   /api/v1/shipping/shippo/standard                  # Standard shipping via Shippo (3 dimensions)
PUT    /api/v1/inventory/{item_id}/dimensions             # Add dimensions to existing items
GET    /api/v1/shipping/savings/{item_id}                # Calculate potential savings for user

# Request/Response Models
class ShippingArbitrageResponse:
    ebay_cost: float                   # eBay's shipping cost
    flipsync_cost: float              # FlipSync's discounted cost via Shippo
    user_savings: float               # 10% discount to user
    flipsync_revenue: float           # FlipSync's profit from arbitrage
    shipping_method: str              # 'poly' or 'standard'
    dimensions_required: List[str]     # Which dimensions needed

class ShippingEstimate:
    seller_zip: str
    item_dimensions: Dict[str, float]  # length, width, height, weight
    zone_estimates: Dict[str, float]   # zone_1: cost, zone_2: cost, etc.
    average_cost: float
    accuracy_level: str                # 'estimated', 'calculated'
    arbitrage_opportunity: bool        # Can FlipSync save money?
```

### **5. Enhanced Product Creation Workflow (CRITICAL REVENUE FEATURE)**
```python
# /api/v1/product-creation/
POST   /api/v1/product-creation/analyze-image            # Enhanced vision pipeline
POST   /api/v1/product-creation/barcode-lookup           # Barcode identification
POST   /api/v1/product-creation/ocr-fallback             # OCR text extraction
POST   /api/v1/product-creation/google-vision            # Google Vision API fallback
POST   /api/v1/product-creation/gemini-research          # Gemini product research
POST   /api/v1/product-creation/ebay-research            # eBay API market research
POST   /api/v1/product-creation/publish-listing          # Publish to eBay
GET    /api/v1/product-creation/workflow/{workflow_id}   # Track workflow progress

# Request/Response Models
class ProductCreationWorkflow:
    workflow_id: str
    image_data: str                    # Base64 image
    barcode_result: Optional[Dict]     # Barcode lookup result
    ocr_result: Optional[Dict]         # OCR extraction result
    google_vision_result: Optional[Dict] # Google Vision result
    gemini_research: Optional[Dict]    # Gemini product analysis
    ebay_research: Optional[Dict]      # eBay market data
    listing_draft: Optional[Dict]      # Generated listing
    publish_status: str               # 'draft', 'published', 'failed'
    revenue_potential: Dict[str, float] # Shipping arbitrage + listing fees
```

### **6. External Advertising System (CRITICAL REVENUE SOURCE)**
```python
# /api/v1/advertising/
POST   /api/v1/advertising/boost-listing                 # Create external ad campaign
GET    /api/v1/advertising/campaigns                     # List active campaigns
PUT    /api/v1/advertising/campaigns/{campaign_id}       # Update campaign
DELETE /api/v1/advertising/campaigns/{campaign_id}       # Cancel campaign
GET    /api/v1/advertising/performance/{campaign_id}     # Campaign performance metrics
POST   /api/v1/advertising/revenue-tracking              # Track FlipSync ad revenue

# Request/Response Models
class ExternalAdCampaign:
    campaign_id: str
    listing_id: str
    ad_platform: str                   # 'facebook', 'google', 'instagram', etc.
    budget: float                      # User's ad spend
    flipsync_fee: float               # FlipSync's revenue from ad management
    performance_metrics: Dict[str, Any]
    roi_estimate: float
    status: str                       # 'active', 'paused', 'completed'
```

### **7. AI-Powered Optimization Score**
```python
# /api/v1/optimization/
GET    /api/v1/optimization/score/{user_id}              # Current optimization score
GET    /api/v1/optimization/opportunities/{user_id}      # Advanced optimization opportunities
POST   /api/v1/optimization/feedback                     # User feedback on optimizations

# Response Model
class OptimizationScore:
    current_score: float               # 0-100 percentage
    score_components: Dict[str, float] # breakdown by category
    opportunities_count: int
    improvement_suggestions: List[str]
    last_calculated: datetime
```

---

## 🔄 **ENHANCED EXISTING ENDPOINTS**

### **1. Agent Status Enhancement**
```python
# /api/v1/agents/status - ENHANCE EXISTING
# Add real-time optimization opportunities count
# Add partnership metrics
# Add agent collaboration indicators

class EnhancedAgentStatus:
    agent_id: str
    status: str
    optimization_opportunities: int    # NEW
    partnership_score: float          # NEW
    collaboration_active: bool        # NEW
    last_optimization: datetime       # NEW
```

### **2. Chat System Enhancement**
```python
# /api/v1/chat/ - ENHANCE EXISTING
# Add buyer communication routing
# Add agent collaboration context
# Add decision support features

class EnhancedChatMessage:
    message_id: str
    content: str
    sender_type: str                   # 'user', 'agent', 'buyer'
    context_type: str                  # 'general', 'buyer_support', 'agent_collab'
    suggested_responses: List[str]     # NEW
    decision_context: Dict[str, Any]   # NEW
```

### **3. WebSocket Events Enhancement**
```python
# /ws/flipsync - ENHANCE EXISTING
# Add new event types for V3 features

class WebSocketEvent:
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    
# New event types needed:
# - 'opportunity_alert'      → Real-time opportunity notifications
# - 'assessment_update'      → Physical assessment progress
# - 'optimization_score'     → AI-Powered Optimization Score updates
# - 'partnership_metric'     → Partnership performance updates
# - 'agent_collaboration'    → Agent-to-agent coordination events
```

---

## 🏗️ **IMPLEMENTATION PRIORITY MATRIX**

### **Phase 1 (Critical - Week 1-3)**
1. **User Profile System** - Required for adaptive content
2. **Enhanced Agent Status** - Required for collaboration hub
3. **WebSocket Enhancements** - Required for real-time features

### **Phase 2 (Revenue Critical - Week 4-7)**
1. **Enhanced Product Creation Workflow** - ESSENTIAL for eBay publishing revenue
   - Barcode → OCR → Google Vision → Gemini → eBay API pipeline
2. **Shipping Arbitrage System** - ESSENTIAL for shipping revenue via Shippo
   - Dimensional shipping, cost comparison, revenue tracking
3. **External Advertising APIs** - ESSENTIAL for ad management revenue
   - Campaign management, performance tracking, revenue optimization

### **Phase 3 (High Priority - Week 8-10)**
1. **Physical Assessment APIs** - Required for assessment workflow
2. **Optimization Score** - Required for partnership dashboard
3. **Adaptive Opportunities** - Required for opportunity center

### **Phase 4 (Enhancement - Week 11-12)**
1. **Enhanced Chat System** - Required for communication hub
2. **Product Specifications** - Required for intelligent completeness
3. **Performance Optimization** - System-wide improvements

---

## 🔌 **INTEGRATION PATTERNS**

### **Frontend Service Pattern**
```dart
// Flutter service implementation pattern
class AdaptiveOpportunityService {
  final ApiClient _apiClient;
  final UserProfileService _userProfile;
  
  Future<List<Opportunity>> getOpportunities() async {
    final profile = await _userProfile.getCurrentProfile();
    final endpoint = '/api/v1/opportunities/${profile.inventorySource}';
    return await _apiClient.get(endpoint);
  }
}
```

### **Real-time Integration Pattern**
```dart
// WebSocket integration for real-time features
class RealTimeCollaborationService {
  final WebSocketService _webSocket;
  
  void subscribeToOptimizationUpdates() {
    _webSocket.subscribe('optimization_score', (data) {
      // Update UI with new optimization score
    });
  }
}
```

### **Error Handling Pattern**
```dart
// Consistent error handling across V3 features
class V3ApiService {
  Future<T> makeRequest<T>(String endpoint) async {
    try {
      return await _apiClient.get(endpoint);
    } on ApiException catch (e) {
      if (e.statusCode == 404 && endpoint.contains('opportunities')) {
        // Fallback to general opportunities
        return await _apiClient.get('/api/v1/opportunities/miscellaneous');
      }
      rethrow;
    }
  }
}
```

---

## 🧪 **TESTING REQUIREMENTS**

### **API Endpoint Testing**
```python
# Backend test requirements
def test_user_profile_inventory_source():
    # Test inventory source preference storage and retrieval
    
def test_adaptive_opportunities_routing():
    # Test different content based on inventory source
    
def test_shipping_zone_calculation():
    # Test USPS zone calculation accuracy
    
def test_optimization_score_calculation():
    # Test AI-Powered Optimization Score algorithm
```

### **Integration Testing**
```dart
// Frontend integration test requirements
testWidgets('Adaptive content loads based on user profile', (tester) async {
  // Test that opportunity center shows different content
  // based on user's inventory source preference
});

testWidgets('Real-time optimization score updates', (tester) async {
  // Test WebSocket integration for live score updates
});
```

---

## 📋 **BACKEND DEVELOPMENT CHECKLIST**

### **Database Schema Updates**
- [ ] User profile table with inventory_source field
- [ ] Opportunity alerts table
- [ ] Assessment workflow tables
- [ ] Shipping zone cache table
- [ ] Optimization score history table

### **API Implementation**
- [ ] User profile CRUD endpoints
- [ ] Adaptive opportunity endpoints
- [ ] Physical assessment workflow endpoints
- [ ] Shipping intelligence endpoints
- [ ] Enhanced WebSocket events

### **Integration Points**
- [ ] eBay API for seller location
- [ ] USPS API for shipping zones
- [ ] Product specification database
- [ ] AI vision service integration
- [ ] Real-time notification system

### **Performance Considerations**
- [ ] Caching for shipping zone calculations
- [ ] Optimization score calculation efficiency
- [ ] WebSocket connection scaling
- [ ] Database query optimization
- [ ] API response time monitoring

This document provides the complete backend requirements for successful V3 implementation with clear priorities and integration patterns.
