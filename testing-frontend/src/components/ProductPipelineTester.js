import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { 
  Camera, 
  FileText, 
  Zap, 
  ShoppingCart, 
  Upload,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Eye
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';

const ProductPipelineTester = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [pipelineData, setPipelineData] = useState({
    barcode: '',
    ocrText: '',
    productData: null,
    optimizedListing: null,
    ebayListing: null
  });
  const [testResults, setTestResults] = useState({});

  const pipelineSteps = [
    {
      id: 'barcode',
      title: 'Barcode Input',
      icon: Camera,
      description: 'Simulate barcode scanning',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      id: 'ocr',
      title: 'OCR Processing',
      icon: FileText,
      description: 'Extract text from product images',
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      id: 'vision',
      title: 'Vision Analysis',
      icon: Eye,
      description: 'Google Vision API product analysis',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      id: 'optimization',
      title: 'Gemini Optimization',
      icon: Zap,
      description: 'AI-powered listing optimization',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      id: 'ebay',
      title: 'eBay Listing',
      icon: ShoppingCart,
      description: 'Create eBay listing',
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    }
  ];

  const sampleProducts = [
    {
      barcode: '123456789012',
      title: 'Apple iPhone 13 Pro Max',
      description: 'Latest iPhone model with advanced camera system',
      category: 'Cell Phones & Smartphones'
    },
    {
      barcode: '987654321098',
      title: 'Sony WH-1000XM4 Headphones',
      description: 'Wireless noise-canceling headphones',
      category: 'Headphones'
    },
    {
      barcode: '456789123456',
      title: 'Nintendo Switch Console',
      description: 'Gaming console with detachable controllers',
      category: 'Video Game Consoles'
    }
  ];

  const runFullPipeline = async () => {
    setIsLoading(true);
    setCurrentStep(0);
    setTestResults({});

    try {
      // Step 1: Barcode Processing
      setCurrentStep(1);
      await simulateStep('barcode', 1000);
      
      // Step 2: OCR Processing
      setCurrentStep(2);
      await simulateOCR();

      // Step 3: Vision Analysis
      setCurrentStep(3);
      const visionResult = await testVisionAnalysis();
      
      // Step 4: Gemini Optimization
      setCurrentStep(4);
      const optimizationResult = await testGeminiOptimization(visionResult);
      
      // Step 5: eBay Listing Creation
      setCurrentStep(5);
      await testEbayListing(optimizationResult);
      
      setCurrentStep(6); // Complete
      toast.success('Full pipeline completed successfully!');
      
    } catch (error) {
      console.error('Pipeline failed:', error);
      toast.error(`Pipeline failed at step ${currentStep}: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const simulateStep = (stepName, delay) => {
    return new Promise(resolve => {
      setTimeout(() => {
        setTestResults(prev => ({
          ...prev,
          [stepName]: {
            success: true,
            timestamp: new Date().toISOString(),
            duration: delay
          }
        }));
        resolve();
      }, delay);
    });
  };

  const simulateOCR = async () => {
    const sampleOCR = "Apple iPhone 13 Pro Max 256GB Unlocked Smartphone";
    setPipelineData(prev => ({ ...prev, ocrText: sampleOCR }));
    
    setTestResults(prev => ({
      ...prev,
      ocr: {
        success: true,
        data: { extractedText: sampleOCR },
        timestamp: new Date().toISOString()
      }
    }));
    
    return sampleOCR;
  };

  const testVisionAnalysis = async () => {
    try {
      const productData = {
        title: pipelineData.barcode || 'Test Product',
        description: pipelineData.ocrText || 'Test product description',
        category: 'Electronics'
      };

      const response = await api.analyzeProduct(productData);
      
      setPipelineData(prev => ({ ...prev, productData: response }));
      setTestResults(prev => ({
        ...prev,
        vision: {
          success: true,
          data: response,
          timestamp: new Date().toISOString()
        }
      }));
      
      return response;
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        vision: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
      throw error;
    }
  };

  const testGeminiOptimization = async (productData) => {
    try {
      const response = await api.generateListing(productData || {
        title: 'Test Product',
        description: 'Test description'
      });
      
      setPipelineData(prev => ({ ...prev, optimizedListing: response }));
      setTestResults(prev => ({
        ...prev,
        optimization: {
          success: true,
          data: response,
          timestamp: new Date().toISOString()
        }
      }));
      
      return response;
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        optimization: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
      throw error;
    }
  };

  const testEbayListing = async (listingData) => {
    try {
      const response = await api.createEbayListing(listingData || {
        title: 'Test eBay Listing',
        description: 'Test listing description',
        price: 99.99
      });
      
      setPipelineData(prev => ({ ...prev, ebayListing: response }));
      setTestResults(prev => ({
        ...prev,
        ebay: {
          success: true,
          data: response,
          timestamp: new Date().toISOString()
        }
      }));
      
      return response;
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        ebay: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
      throw error;
    }
  };

  const loadSampleProduct = (product) => {
    setPipelineData(prev => ({
      ...prev,
      barcode: product.barcode,
      ocrText: `${product.title} - ${product.description}`
    }));
    toast.success(`Loaded sample product: ${product.title}`);
  };

  const getStepStatus = (stepIndex) => {
    if (currentStep > stepIndex) return 'complete';
    if (currentStep === stepIndex && isLoading) return 'active';
    return 'pending';
  };

  const getStepIcon = (step, stepIndex) => {
    const status = getStepStatus(stepIndex);
    const Icon = step.icon;
    
    if (status === 'complete') {
      return <CheckCircle className="w-6 h-6 text-green-500" />;
    } else if (status === 'active') {
      return <Clock className="w-6 h-6 text-blue-500 animate-pulse" />;
    } else {
      return <Icon className={`w-6 h-6 ${step.color}`} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Product Creation Pipeline</h2>
          <p className="text-gray-600 mt-1">
            Test the complete product creation workflow: Barcode → OCR → Vision → Gemini → eBay
          </p>
        </div>
        <button
          onClick={runFullPipeline}
          disabled={isLoading}
          className="btn-primary disabled:opacity-50"
        >
          <Play className="w-4 h-4 mr-2" />
          {isLoading ? 'Running Pipeline...' : 'Run Full Pipeline'}
        </button>
      </div>

      {/* Sample Products */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sample Products</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {sampleProducts.map((product, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900">{product.title}</h4>
              <p className="text-sm text-gray-600 mt-1">{product.description}</p>
              <p className="text-xs text-gray-500 mt-2">Barcode: {product.barcode}</p>
              <button
                onClick={() => loadSampleProduct(product)}
                className="mt-3 btn-secondary text-sm"
              >
                <Upload className="w-3 h-3 mr-1" />
                Load
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Pipeline Progress</h3>
        <div className="space-y-4">
          {pipelineSteps.map((step, index) => {
            const status = getStepStatus(index + 1);
            
            return (
              <div key={step.id} className={`flex items-center p-4 rounded-lg border-2 ${
                status === 'complete' ? 'border-green-200 bg-green-50' :
                status === 'active' ? 'border-blue-200 bg-blue-50' :
                'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex-shrink-0 mr-4">
                  {getStepIcon(step, index + 1)}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{step.title}</h4>
                  <p className="text-sm text-gray-600">{step.description}</p>
                </div>
                <div className="flex-shrink-0">
                  {testResults[step.id] && (
                    <div className="text-right">
                      {testResults[step.id].success ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Pipeline Data */}
      {Object.keys(pipelineData).some(key => pipelineData[key]) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Pipeline Data</h3>
          <ReactJsonView
            src={pipelineData}
            theme="rjv-default"
            collapsed={1}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={true}
            name="pipeline_data"
          />
        </div>
      )}

      {/* Test Results */}
      {Object.keys(testResults).length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
          <ReactJsonView
            src={testResults}
            theme="rjv-default"
            collapsed={1}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={true}
            name="test_results"
          />
        </div>
      )}
    </div>
  );
};

export default ProductPipelineTester;
