import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react';

const EbayOAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Processing eBay OAuth callback...');
  const [details, setDetails] = useState(null);

  useEffect(() => {
    handleOAuthCallback();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleOAuthCallback = async () => {
    try {
      // Get parameters from URL
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (error) {
        setStatus('error');
        setMessage(`eBay OAuth Error: ${error}`);
        setDetails({ error, error_description: errorDescription });
        toast.error(`eBay OAuth failed: ${error}`);
        return;
      }

      if (!code) {
        setStatus('error');
        setMessage('No authorization code received from eBay');
        toast.error('OAuth callback missing authorization code');
        return;
      }

      setMessage('Exchanging authorization code for access token...');

      // Here we would normally send the code to our backend to exchange for tokens
      // For now, we'll simulate the process and show the received data
      
      const callbackData = {
        code,
        state,
        timestamp: new Date().toISOString(),
        url: window.location.href
      };

      setDetails(callbackData);
      setStatus('success');
      setMessage('eBay OAuth callback received successfully!');
      
      toast.success('eBay OAuth callback processed successfully');
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate('/?tab=ebay');
      }, 3000);

    } catch (error) {
      console.error('OAuth callback error:', error);
      setStatus('error');
      setMessage(`Failed to process OAuth callback: ${error.message}`);
      toast.error('OAuth callback processing failed');
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-16 h-16 text-green-500" />;
      case 'error':
        return <XCircle className="w-16 h-16 text-red-500" />;
      default:
        return <RefreshCw className="w-16 h-16 text-blue-500 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-blue-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FlipSync</h1>
          <h2 className="text-xl font-semibold text-gray-700">eBay OAuth Callback</h2>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="mb-6">
            {getStatusIcon()}
          </div>

          <h3 className={`text-lg font-semibold mb-4 ${getStatusColor()}`}>
            {status === 'processing' && 'Processing...'}
            {status === 'success' && 'Success!'}
            {status === 'error' && 'Error'}
          </h3>

          <p className="text-gray-600 mb-6">{message}</p>

          {status === 'success' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-green-800 text-sm">
                eBay authorization received successfully. You will be redirected to the dashboard shortly.
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800 text-sm">
                There was an issue processing the eBay OAuth callback. Please try again.
              </p>
            </div>
          )}

          {details && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-left">
              <h4 className="font-medium text-gray-900 mb-2">Callback Details:</h4>
              <div className="text-sm text-gray-600 space-y-1">
                {details.code && (
                  <div>
                    <span className="font-medium">Authorization Code:</span>
                    <div className="font-mono text-xs bg-gray-100 p-1 rounded mt-1 break-all">
                      {details.code}
                    </div>
                  </div>
                )}
                {details.state && (
                  <div>
                    <span className="font-medium">State:</span> {details.state}
                  </div>
                )}
                {details.error && (
                  <div>
                    <span className="font-medium">Error:</span> {details.error}
                  </div>
                )}
                {details.error_description && (
                  <div>
                    <span className="font-medium">Description:</span> {details.error_description}
                  </div>
                )}
                <div>
                  <span className="font-medium">Timestamp:</span> {details.timestamp}
                </div>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              onClick={() => navigate('/')}
              className="flex-1 btn-primary"
            >
              Go to Dashboard
            </button>
            {status === 'error' && (
              <button
                onClick={() => window.location.reload()}
                className="flex-1 btn-secondary"
              >
                Retry
              </button>
            )}
          </div>
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-500">
            FlipSync Testing Dashboard - eBay OAuth Integration
          </p>
        </div>
      </div>
    </div>
  );
};

export default EbayOAuthCallback;
