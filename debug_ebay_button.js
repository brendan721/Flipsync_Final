// Debug script to monitor eBay connect button clicks
// Inject this into the browser console to debug the popup issue

console.log('🔧 eBay Connect Button Debug Script Loaded');

// Override window.open to monitor popup attempts
const originalWindowOpen = window.open;
window.open = function(...args) {
    console.log('🔄 [DEBUG] window.open() called with args:', args);
    console.log('🔄 [DEBUG] URL:', args[0]);
    console.log('🔄 [DEBUG] Target:', args[1]);
    console.log('🔄 [DEBUG] Features:', args[2]);
    
    const result = originalWindowOpen.apply(this, args);
    console.log('🔄 [DEBUG] window.open() result:', result);
    
    if (!result) {
        console.error('❌ [DEBUG] Popup was blocked or failed to open');
        console.log('💡 [DEBUG] Check browser popup settings');
    } else {
        console.log('✅ [DEBUG] Popup opened successfully');
    }
    
    return result;
};

// Monitor fetch requests to see if OAuth URL is being fetched
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    const options = args[1] || {};
    
    if (url.includes('ebay') || url.includes('oauth')) {
        console.log('🔄 [DEBUG] eBay/OAuth fetch request:', url);
        console.log('🔄 [DEBUG] Fetch options:', options);
    }
    
    return originalFetch.apply(this, args).then(response => {
        if (url.includes('ebay') || url.includes('oauth')) {
            console.log('🔄 [DEBUG] eBay/OAuth fetch response:', response.status, response.statusText);
            if (!response.ok) {
                console.error('❌ [DEBUG] eBay/OAuth fetch failed:', response.status, response.statusText);
            }
        }
        return response;
    }).catch(error => {
        if (url.includes('ebay') || url.includes('oauth')) {
            console.error('❌ [DEBUG] eBay/OAuth fetch error:', error);
        }
        throw error;
    });
};

// Monitor button clicks
document.addEventListener('click', function(event) {
    const target = event.target;
    const text = target.textContent || target.innerText || '';
    
    if (text.toLowerCase().includes('ebay') || text.toLowerCase().includes('connect')) {
        console.log('🔄 [DEBUG] Potential eBay button clicked:', target);
        console.log('🔄 [DEBUG] Button text:', text);
        console.log('🔄 [DEBUG] Button element:', target);
        console.log('🔄 [DEBUG] Button classes:', target.className);
        console.log('🔄 [DEBUG] Button ID:', target.id);
        
        // Add a small delay to see if popup opens
        setTimeout(() => {
            console.log('🔄 [DEBUG] Checking for popup after button click...');
        }, 100);
    }
});

// Monitor console errors
const originalConsoleError = console.error;
console.error = function(...args) {
    if (args.some(arg => String(arg).toLowerCase().includes('popup') || 
                         String(arg).toLowerCase().includes('ebay') ||
                         String(arg).toLowerCase().includes('oauth'))) {
        console.log('🚨 [DEBUG] Relevant error detected:', args);
    }
    return originalConsoleError.apply(this, args);
};

// Test popup blocker status
function testPopupBlocker() {
    console.log('🔄 [DEBUG] Testing popup blocker status...');
    const testPopup = window.open('', 'test', 'width=1,height=1');
    if (testPopup) {
        testPopup.close();
        console.log('✅ [DEBUG] Popups are allowed');
        return true;
    } else {
        console.error('❌ [DEBUG] Popups are blocked');
        return false;
    }
}

// Test backend connectivity
async function testBackendConnectivity() {
    console.log('🔄 [DEBUG] Testing backend connectivity...');
    try {
        const response = await fetch('http://localhost:8001/api/v1/health');
        if (response.ok) {
            console.log('✅ [DEBUG] Backend is accessible');
            return true;
        } else {
            console.error('❌ [DEBUG] Backend returned error:', response.status);
            return false;
        }
    } catch (error) {
        console.error('❌ [DEBUG] Backend connection failed:', error);
        return false;
    }
}

// Test eBay OAuth endpoint
async function testEbayOAuthEndpoint() {
    console.log('🔄 [DEBUG] Testing eBay OAuth endpoint...');
    try {
        const response = await fetch('http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scopes: ['https://api.ebay.com/oauth/api_scope']
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ [DEBUG] eBay OAuth endpoint working');
            console.log('🔄 [DEBUG] OAuth URL received:', data.data?.authorization_url?.substring(0, 100) + '...');
            return data.data?.authorization_url;
        } else {
            console.error('❌ [DEBUG] eBay OAuth endpoint failed:', response.status);
            return null;
        }
    } catch (error) {
        console.error('❌ [DEBUG] eBay OAuth endpoint error:', error);
        return null;
    }
}

// Run initial tests
console.log('🚀 [DEBUG] Running initial diagnostics...');
testPopupBlocker();
testBackendConnectivity();

// Provide manual test functions
window.debugEbay = {
    testPopupBlocker,
    testBackendConnectivity,
    testEbayOAuthEndpoint,
    async testFullFlow() {
        console.log('🚀 [DEBUG] Testing full eBay OAuth flow...');
        
        const popupAllowed = testPopupBlocker();
        if (!popupAllowed) {
            console.error('❌ [DEBUG] Cannot test - popups are blocked');
            return;
        }
        
        const backendOk = await testBackendConnectivity();
        if (!backendOk) {
            console.error('❌ [DEBUG] Cannot test - backend not accessible');
            return;
        }
        
        const oauthUrl = await testEbayOAuthEndpoint();
        if (!oauthUrl) {
            console.error('❌ [DEBUG] Cannot test - OAuth URL not available');
            return;
        }
        
        console.log('🔄 [DEBUG] Opening test popup with OAuth URL...');
        const popup = window.open(oauthUrl, 'ebay-test', 'width=600,height=700');
        if (popup) {
            console.log('✅ [DEBUG] Test popup opened successfully!');
        } else {
            console.error('❌ [DEBUG] Test popup failed to open');
        }
    }
};

console.log('✅ [DEBUG] Debug script ready!');
console.log('💡 [DEBUG] Use debugEbay.testFullFlow() to test the complete flow');
console.log('💡 [DEBUG] Click the eBay connect button to see detailed logs');
