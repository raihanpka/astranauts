/**
 * Astranauts API Configuration for Frontend Integration
 * 
 * This configuration file provides the base URLs and endpoints
 * for integrating with the Astranauts API from Next.js frontend.
 */

export const API_CONFIG = {
  // Base URLs for different environments
  BASE_URL: {
    development:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080",
    production:
      process.env.NEXT_PUBLIC_API_BASE_URL || "https://astranauts-api-xxxxxxx.run.app",
    staging:
      process.env.NEXT_PUBLIC_API_STAGING_URL || "https://staging-astranauts-api-xxxxxxx.run.app",
  },

  // Module-specific URLs
  MODULE_URLS: {
    PRABU:
      process.env.NEXT_PUBLIC_PRABU_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/prabu",
    SARANA:
      process.env.NEXT_PUBLIC_SARANA_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/sarana",
    SETIA:
      process.env.NEXT_PUBLIC_SETIA_API_URL ||
      "https://astranauts-api-xxxxxxx.run.app/api/v1/setia",
  },

  // API Endpoints
  ENDPOINTS: {
    // Global Health Checks
    GLOBAL: {
      HEALTH_CHECK: "/health",
      API_V1_HEALTH: "/api/v1/health",
      DOCS: "/docs",
      REDOC: "/redoc",
    },

    // PRABU Module (Credit Scoring)
    PRABU: {
      HEALTH_CHECK: "/health",
      CALCULATE_SCORE: "/calculate",
      ALTMAN_Z_SCORE: "/altman-z", 
      M_SCORE: "/m-score",
      FINANCIAL_METRICS: "/metrics",
    },

    // SARANA Module (OCR & NLP)
    SARANA: {
      HEALTH_CHECK: "/health",
      DOCUMENT_PARSE: "/document/parse",
      OCR_UPLOAD: "/ocr/upload",
      EXTRACT_DATA: "/extract",
      // Document management endpoints
      GET_DOCUMENTS: "/documents",
      GET_DOCUMENT_DETAIL: "/documents/{id}",
      GET_EXTRACTED_TEXT: "/documents/{id}/extracted-text",
      GET_FINANCIAL_DATA: "/documents/{id}/financial-data",
      GET_STATS: "/stats",
      // Company-based endpoints
      GET_COMPANIES: "/companies",
      GET_COMPANY_DOCUMENTS: "/companies/{company_identifier}/documents",
      GET_COMPANY_LATEST: "/companies/{company_identifier}/latest",
      GET_COMPANY_FINANCIAL_DATA: "/companies/{company_identifier}/financial-data",
    },

    // SETIA Module (Sentiment Analysis)
    SETIA: {
      HEALTH_CHECK: "/health",
      SENTIMENT_ANALYSIS: "/sentiment",
      NEWS_MONITORING: "/news",
      EXTERNAL_RISK: "/external-risk",
    },
  },

  // Request configurations
  DEFAULT_HEADERS: {
    "Content-Type": "application/json",
    "Accept": "application/json",
  },

  // Timeout configurations (in milliseconds)
  TIMEOUTS: {
    DEFAULT: 30000,  // 30 seconds
    UPLOAD: 120000,  // 2 minutes for file uploads
    ANALYSIS: 180000, // 3 minutes for complex analysis
  },
};

/**
 * Helper function to get the appropriate base URL based on environment
 */
export const getBaseUrl = () => {
  const env = process.env.NODE_ENV || 'development';
  return API_CONFIG.BASE_URL[env] || API_CONFIG.BASE_URL.development;
};

/**
 * Helper function to construct full API URLs
 */
export const buildApiUrl = (module, endpoint) => {
  const baseUrl = getBaseUrl();
  const modulePrefix = `/api/v1/${module.toLowerCase()}`;
  return `${baseUrl}${modulePrefix}${endpoint}`;
};

/**
 * Predefined API client configurations
 */
export const API_CLIENTS = {
  prabu: {
    baseURL: `${getBaseUrl()}/api/v1/prabu`,
    timeout: API_CONFIG.TIMEOUTS.ANALYSIS,
    headers: API_CONFIG.DEFAULT_HEADERS,
  },
  sarana: {
    baseURL: `${getBaseUrl()}/api/v1/sarana`,
    timeout: API_CONFIG.TIMEOUTS.UPLOAD,
    headers: {
      // Note: For file uploads, don't set Content-Type
      // Let the browser set it with boundary for multipart/form-data
      "Accept": "application/json",
    },
  },
  setia: {
    baseURL: `${getBaseUrl()}/api/v1/setia`,
    timeout: API_CONFIG.TIMEOUTS.ANALYSIS,
    headers: API_CONFIG.DEFAULT_HEADERS,
  },
};

/**
 * Example usage functions for each module
 */
export const API_EXAMPLES = {
  // PRABU - Credit Scoring
  prabu: {
    calculateScore: (financialData) => ({
      url: buildApiUrl('prabu', API_CONFIG.ENDPOINTS.PRABU.CALCULATE_SCORE),
      method: 'POST',
      body: JSON.stringify(financialData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
    
    altmanZScore: (financialData) => ({
      url: buildApiUrl('prabu', API_CONFIG.ENDPOINTS.PRABU.ALTMAN_Z_SCORE),
      method: 'POST',
      body: JSON.stringify(financialData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
  },

  // SARANA - OCR & NLP
  sarana: {
    parseDocument: (file, options = {}) => {
      const formData = new FormData();
      formData.append('file', file);
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value);
      });
      
      return {
        url: buildApiUrl('sarana', API_CONFIG.ENDPOINTS.SARANA.DOCUMENT_PARSE),
        method: 'POST',
        body: formData,
        // Don't set Content-Type header for FormData
      };
    },

    ocrUpload: (file, ocrEngine = 'tesseract') => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('ocr_engine', ocrEngine);
      
      return {
        url: buildApiUrl('sarana', API_CONFIG.ENDPOINTS.SARANA.OCR_UPLOAD),
        method: 'POST',
        body: formData,
      };
    },
  },

  // SETIA - Sentiment Analysis
  setia: {
    sentimentAnalysis: (companyData) => ({
      url: buildApiUrl('setia', API_CONFIG.ENDPOINTS.SETIA.SENTIMENT_ANALYSIS),
      method: 'POST',
      body: JSON.stringify(companyData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),

    newsMonitoring: (companyData) => ({
      url: buildApiUrl('setia', API_CONFIG.ENDPOINTS.SETIA.NEWS_MONITORING),
      method: 'POST',
      body: JSON.stringify(companyData),
      headers: API_CONFIG.DEFAULT_HEADERS,
    }),
  },
};

/**
 * Enhanced API Client compatible with backend code
 * Provides company-based document management
 */
export class EnhancedBackendAPIClient {
  static async parseFinancialDocumentWithCompany(file, companyIdentifier, options = {}) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('company_identifier', companyIdentifier)
      formData.append('output_format', options.outputFormat || 'structured_json')
      formData.append('ocr_engine', options.ocrEngine || 'tesseract')
      formData.append('pdf_parsing_method', options.pdfParsingMethod || 'pymupdf')
      formData.append('jenis_pengaju', options.jenisPengaju || 'korporat')

      const response = await fetch(`${getBaseUrl()}${API_CONFIG.ENDPOINTS.SARANA.DOCUMENT_PARSE}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Financial parsing error: ${response.status}`)
      }

      const result = await response.json()
      
      return {
        success: true,
        data: {
          documentId: result.document_id,
          companyIdentifier: companyIdentifier,
          currentYear: result.hasil_ekstraksi_semua_dokumen || [],
          previousYear: result.hasil_ekstraksi_semua_dokumen_t_minus_1 || [],
          extractedText: result.extracted_text || "",
          processingTime: result.processing_time_seconds || 0,
          financialKeywords: result.financial_keywords_data || {}
        }
      }
    } catch (error) {
      console.error('Enhanced financial document parsing error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  static async getLatestFinancialDataByCompany(companyIdentifier) {
    try {
      const url = `${getBaseUrl()}${API_CONFIG.ENDPOINTS.SARANA.GET_COMPANY_FINANCIAL_DATA}`.replace('{company_identifier}', companyIdentifier)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: API_CONFIG.DEFAULT_HEADERS,
      })

      if (response.status === 404) {
        return {
          success: false,
          error: `No financial data found for company: ${companyIdentifier}`
        }
      }

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      
      return {
        success: true,
        data: {
          companyIdentifier: result.company_identifier,
          documentId: result.document_id,
          fileName: result.original_filename,
          createdAt: result.created_at,
          processingTime: result.processing_time_seconds,
          structuredData: result.structured_data || {},
          financialKeywords: result.financial_keywords || {},
          // Parse untuk kompatibilitas dengan kode lama
          currentYear: this.parseStructuredDataToArray(result.structured_data?.current || {}),
          previousYear: this.parseStructuredDataToArray(result.structured_data?.previous || {})
        }
      }
    } catch (error) {
      console.error('Get latest financial data error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  static async getAllCompanies() {
    try {
      const response = await fetch(`${getBaseUrl()}${API_CONFIG.ENDPOINTS.SARANA.GET_COMPANIES}`, {
        method: 'GET',
        headers: API_CONFIG.DEFAULT_HEADERS,
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      
      return {
        success: true,
        data: {
          companies: result.companies,
          totalCompanies: result.total_companies
        }
      }
    } catch (error) {
      console.error('Get all companies error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  static async getCompanyDocuments(companyIdentifier, limit = 20, offset = 0) {
    try {
      const url = `${getBaseUrl()}${API_CONFIG.ENDPOINTS.SARANA.GET_COMPANY_DOCUMENTS}`.replace('{company_identifier}', companyIdentifier)
      
      const response = await fetch(`${url}?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: API_CONFIG.DEFAULT_HEADERS,
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      
      return {
        success: true,
        data: result
      }
    } catch (error) {
      console.error('Get company documents error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // Helper function untuk parsing structured data ke format array yang kompatibel
  static parseStructuredDataToArray(structuredData) {
    if (!structuredData || typeof structuredData !== 'object') {
      return []
    }

    return [{
      nama_file: "structured_data",
      hasil_ekstraksi: structuredData
    }]
  }

  // Wrapper functions untuk kompatibilitas dengan kode lama
  static async parseFinancialDocument(file, companyIdentifier = null) {
    // Jika companyIdentifier tidak diberikan, ekstrak dari nama file
    if (!companyIdentifier && file.name) {
      companyIdentifier = file.name.split('.')[0].replace(/[_-]/g, ' ').trim()
    }
    
    return this.parseFinancialDocumentWithCompany(file, companyIdentifier || 'unknown_company')
  }

  // Legacy functions untuk kompatibilitas
  static formatCurrency(amount) {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  static formatPercentage(ratio) {
    if (ratio === null || ratio === undefined) return 'N/A'
    return `${(ratio * 100).toFixed(2)}%`
  }

  static formatRatio(ratio) {
    if (ratio === null || ratio === undefined) return 'N/A'
    return ratio.toFixed(2)
  }

  static calculateRatios(metrics) {
    if (!metrics) return {}
    
    return {
      currentRatio: metrics.currentAssets && metrics.currentLiabilities 
        ? metrics.currentAssets / metrics.currentLiabilities : null,
      debtToEquityRatio: metrics.totalLiabilities && metrics.totalEquity
        ? metrics.totalLiabilities / metrics.totalEquity : null,
      returnOnAssets: metrics.netIncome && metrics.totalAssets
        ? metrics.netIncome / metrics.totalAssets : null,
      returnOnEquity: metrics.netIncome && metrics.totalEquity
        ? metrics.netIncome / metrics.totalEquity : null,
      grossProfitMargin: metrics.grossProfit && metrics.netRevenue
        ? metrics.grossProfit / metrics.netRevenue : null,
      netProfitMargin: metrics.netIncome && metrics.netRevenue
        ? metrics.netIncome / metrics.netRevenue : null
    }
  }
}

// Export enhanced functions
export const parseFinancialDocumentWithCompany = EnhancedBackendAPIClient.parseFinancialDocumentWithCompany
export const getLatestFinancialDataByCompany = EnhancedBackendAPIClient.getLatestFinancialDataByCompany
export const getAllCompanies = EnhancedBackendAPIClient.getAllCompanies
export const getCompanyDocuments = EnhancedBackendAPIClient.getCompanyDocuments

// Export legacy compatibility functions
export const parseFinancialDocument = EnhancedBackendAPIClient.parseFinancialDocument
export const formatCurrency = EnhancedBackendAPIClient.formatCurrency
export const formatPercentage = EnhancedBackendAPIClient.formatPercentage
export const formatRatio = EnhancedBackendAPIClient.formatRatio
export const calculateRatios = EnhancedBackendAPIClient.calculateRatios

export default API_CONFIG;
