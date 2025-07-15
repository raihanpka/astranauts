from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, List
import os
import shutil
import uuid

# Impor layanan Sarana dan model Pydantic
from ..services import sarana_service
from ..services.sarana_datastore import sarana_store
from ..models.api_models import (
    SaranaParseDocumentResponse, SaranaDocumentListResponse,
    SaranaDocumentDetail, SaranaProcessingStats, SaranaCompanyDocuments,
    SaranaCompanyListResponse, SaranaCompanyInfo
)

router = APIRouter()

# Direktori temporer untuk menyimpan file upload
TEMP_UPLOAD_DIR_SARANA = "temp_sarana_uploads" 
os.makedirs(TEMP_UPLOAD_DIR_SARANA, exist_ok=True)

# Health check endpoint
@router.get("/health", summary="Sarana Health Check")
async def sarana_health_check():
    """Health check untuk module Sarana"""
    return {"status": "ok", "module": "Sarana", "message": "OCR & NLP module is running"}

@router.post("/document/parse", summary="Parse Financial Documents", response_model=SaranaParseDocumentResponse)
async def parse_document_endpoint(
    file: UploadFile = File(..., description="File dokumen yang akan di-parse"),
    company_identifier: str = Form(..., description="Identifier perusahaan (nama, NPWP, atau kode unik)"),
    file_type: Optional[str] = Form(None, description="Tipe file eksplisit"),
    ocr_engine: str = Form('tesseract', description="Mesin OCR: 'tesseract', 'easyocr', 'ollama'"),
    pdf_parsing_method: str = Form('pymupdf', description="Metode parsing PDF: 'pymupdf', 'pdfplumber'"),
    output_format: str = Form('text', description="Format output: 'text' atau 'structured_json'"),
    jenis_pengaju: str = Form('korporat', description="Jenis pengaju: 'korporat' atau 'individu'"),
    # Parameter tambahan untuk Ollama
    ollama_json_prompt_template: Optional[str] = Form(None, description="Template prompt JSON kustom untuk Ollama"),
    ollama_vision_model_name: str = Form("llama3.2-vision", description="Model vision Ollama"),
    ollama_llm_model_json_name: str = Form("llama3", description="Model LLM Ollama untuk ekstraksi JSON"),
    ollama_api_base_url_param: Optional[str] = Form(None, description="Base URL Ollama API kustom")
):
    """
    Endpoint untuk mem-parsing dokumen keuangan menggunakan modul Sarana.
    Mendukung berbagai format file dan opsi parsing.
    """
    # Buat nama file unik
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        # Simpan file yang di-upload ke direktori temporer
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Panggil layanan Sarana
        parsing_result_dict = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            file_type=file_type,
            ocr_engine=ocr_engine,
            pdf_parsing_method=pdf_parsing_method,
            output_format=output_format,
            jenis_pengaju=jenis_pengaju,
            ollama_json_prompt_template=ollama_json_prompt_template,
            ollama_vision_model_name=ollama_vision_model_name,
            ollama_llm_model_json_name=ollama_llm_model_json_name,
            ollama_api_base_url_param=ollama_api_base_url_param
        )

        if parsing_result_dict.get("error"):
            raise HTTPException(status_code=422, detail=f"Error dalam parsing dokumen: {parsing_result_dict['error']}")

        # Simpan hasil parsing ke database
        document_data = {
            "original_filename": original_filename,
            "file_type": file_type or "auto-detected",
            "ocr_engine": ocr_engine,
            "pdf_parsing_method": pdf_parsing_method,
            "output_format": output_format,
            "jenis_pengaju": jenis_pengaju,
            "extracted_text": parsing_result_dict.get("extracted_text", ""),
            "financial_keywords_data": parsing_result_dict.get("financial_keywords_data", {}),
            "processing_time_seconds": parsing_result_dict.get("processing_time_seconds", 0),
            "file_size_bytes": os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0
        }
        
        # Tambahkan structured_data jika ada
        if "structured_data" in parsing_result_dict:
            document_data["structured_data"] = parsing_result_dict["structured_data"]
        
        # Simpan ke database dan dapatkan ID dengan company_identifier
        doc_id = sarana_store.add_document(document_data, company_identifier)
        
        # Tambahkan document_id ke response
        parsing_result_dict["document_id"] = doc_id
        
        return SaranaParseDocumentResponse(**parsing_result_dict)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Bersihkan file temporer
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/ocr/upload", summary="OCR File Upload")
async def ocr_upload_endpoint(
    file: UploadFile = File(..., description="File untuk OCR (gambar/PDF)"),
    ocr_engine: str = Form('tesseract', description="Mesin OCR: 'tesseract', 'easyocr', 'ollama'")
):
    """
    Endpoint khusus untuk OCR file upload.
    """
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Simplified OCR processing
        parsing_result = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            ocr_engine=ocr_engine,
            output_format='text'
        )

        if parsing_result.get("error"):
            raise HTTPException(status_code=422, detail=f"OCR Error: {parsing_result['error']}")

        return {
            "status": "success",
            "filename": original_filename,
            "ocr_engine": ocr_engine,
            "extracted_text": parsing_result.get("extracted_text", ""),
            "processing_time": parsing_result.get("processing_time_seconds", 0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/extract", summary="Extract Data from Document")
async def extract_data_endpoint(
    file: UploadFile = File(..., description="File untuk ekstraksi data"),
    extraction_type: str = Form('financial', description="Tipe ekstraksi: 'financial', 'general'"),
    output_format: str = Form('structured_json', description="Format output: 'text' atau 'structured_json'")
):
    """
    Endpoint untuk ekstraksi data terstruktur dari dokumen.
    """
    original_filename = file.filename if file.filename else "unknown_file"
    safe_filename_base = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in original_filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename_base}"
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR_SARANA, unique_filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Data extraction processing
        extraction_result = sarana_service.parse_document_sarana(
            file_path=temp_file_path,
            output_format=output_format,
            jenis_pengaju='korporat' if extraction_type == 'financial' else 'individu'
        )

        if extraction_result.get("error"):
            raise HTTPException(status_code=422, detail=f"Extraction Error: {extraction_result['error']}")

        return {
            "status": "success",
            "filename": original_filename,
            "extraction_type": extraction_type,
            "extracted_data": extraction_result.get("extracted_text", ""),
            "processing_time": extraction_result.get("processing_time_seconds", 0)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data extraction error: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# GET Endpoints untuk mengambil data yang tersimpan

@router.get("/documents", summary="Get All Parsed Documents", response_model=SaranaDocumentListResponse)
async def get_all_documents(
    limit: int = Query(20, description="Jumlah maksimum dokumen yang dikembalikan", ge=1, le=100),
    offset: int = Query(0, description="Offset untuk pagination", ge=0),
    filename: Optional[str] = Query(None, description="Filter berdasarkan nama file"),
    file_type: Optional[str] = Query(None, description="Filter berdasarkan tipe file")
):
    """
    Endpoint untuk mengambil semua dokumen yang pernah diparse.
    Mendukung pagination dan filtering.
    """
    try:
        if filename or file_type:
            # Search with filters
            documents = sarana_store.search_documents(filename=filename, file_type=file_type)
            
            # Apply pagination to search results
            total = len(documents)
            paginated_docs = documents[offset:offset + limit]
            
            return {
                "documents": paginated_docs,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
                "filters": {
                    "filename": filename,
                    "file_type": file_type
                }
            }
        else:
            # Get all documents with pagination
            result = sarana_store.get_all_documents(limit=limit, offset=offset)
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.get("/documents/{document_id}", summary="Get Document by ID", response_model=SaranaDocumentDetail)
async def get_document_by_id(document_id: str):
    """
    Endpoint untuk mengambil dokumen spesifik berdasarkan ID.
    """
    try:
        document = sarana_store.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@router.get("/documents/{document_id}/extracted-text", summary="Get Extracted Text Only")
async def get_extracted_text(document_id: str):
    """
    Endpoint untuk mengambil hanya teks yang diekstrak dari dokumen.
    """
    try:
        document = sarana_store.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found")
        
        return {
            "document_id": document_id,
            "original_filename": document.get("original_filename"),
            "extracted_text": document.get("extracted_text", ""),
            "processing_time_seconds": document.get("processing_time_seconds", 0),
            "created_at": document.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted text: {str(e)}")

@router.get("/documents/{document_id}/financial-data", summary="Get Financial Keywords Data")
async def get_financial_data(document_id: str):
    """
    Endpoint untuk mengambil data kata kunci keuangan yang diekstrak.
    """
    try:
        document = sarana_store.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found")
        
        return {
            "document_id": document_id,
            "original_filename": document.get("original_filename"),
            "financial_keywords_data": document.get("financial_keywords_data", {}),
            "structured_data": document.get("structured_data", {}),
            "jenis_pengaju": document.get("jenis_pengaju"),
            "created_at": document.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving financial data: {str(e)}")

@router.get("/stats", summary="Get Sarana Processing Statistics", response_model=SaranaProcessingStats)
async def get_processing_stats():
    """
    Endpoint untuk mendapatkan statistik pemrosesan dokumen.
    """
    try:
        all_docs = sarana_store.get_all_documents(limit=1000)["documents"]
        
        # Calculate statistics
        total_documents = len(all_docs)
        
        # Group by file type
        file_types = {}
        ocr_engines = {}
        processing_times = []
        
        for doc in all_docs:
            # File types
            file_type = doc.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # OCR engines
            ocr_engine = doc.get("ocr_engine", "unknown")
            ocr_engines[ocr_engine] = ocr_engines.get(ocr_engine, 0) + 1
            
            # Processing times
            proc_time = doc.get("processing_time_seconds", 0)
            if isinstance(proc_time, (int, float)) and proc_time > 0:
                processing_times.append(proc_time)
        
        # Calculate average processing time
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_documents": total_documents,
            "file_types": file_types,
            "ocr_engines_used": ocr_engines,
            "average_processing_time_seconds": round(avg_processing_time, 2),
            "fastest_processing_time": min(processing_times) if processing_times else 0,
            "slowest_processing_time": max(processing_times) if processing_times else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

# Company-based endpoints
@router.get("/companies", summary="Get All Companies", response_model=SaranaCompanyListResponse)
async def get_all_companies():
    """
    Mendapatkan daftar semua perusahaan dan statistik dokumen mereka.
    """
    try:
        companies_data = sarana_store.get_all_companies()
        
        return SaranaCompanyListResponse(
            companies=[SaranaCompanyInfo(**company) for company in companies_data],
            total_companies=len(companies_data)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")

@router.get("/companies/{company_identifier}/documents", summary="Get Documents by Company", response_model=SaranaCompanyDocuments)
async def get_documents_by_company(
    company_identifier: str,
    limit: int = Query(default=20, le=100, description="Number of documents to return"),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip")
):
    """
    Mendapatkan semua dokumen untuk perusahaan tertentu.
    """
    try:
        result = sarana_store.get_documents_by_company(company_identifier, limit, offset)
        
        documents = [SaranaDocumentDetail(**doc) for doc in result["documents"]]
        
        return SaranaCompanyDocuments(
            company_identifier=company_identifier,
            documents=documents,
            total=result["total"],
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving company documents: {str(e)}")

@router.get("/companies/{company_identifier}/latest", summary="Get Latest Document by Company", response_model=SaranaDocumentDetail)
async def get_latest_document_by_company(company_identifier: str):
    """
    Mendapatkan dokumen terbaru untuk perusahaan tertentu.
    Berguna untuk mendapatkan data finansial terkini dari perusahaan.
    """
    try:
        document = sarana_store.get_latest_document_by_company(company_identifier)
        
        if not document:
            raise HTTPException(
                status_code=404, 
                detail=f"No documents found for company: {company_identifier}"
            )
        
        return SaranaDocumentDetail(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest document: {str(e)}")

@router.get("/companies/{company_identifier}/financial-data", summary="Get Latest Financial Data by Company")
async def get_latest_financial_data_by_company(company_identifier: str):
    """
    Mendapatkan data finansial terbaru untuk perusahaan tertentu.
    Endpoint khusus untuk integrasi frontend yang membutuhkan data finansial terstruktur.
    """
    try:
        document = sarana_store.get_latest_document_by_company(company_identifier)
        
        if not document:
            raise HTTPException(
                status_code=404, 
                detail=f"No financial data found for company: {company_identifier}"
            )
        
        # Extract financial data based on available formats
        financial_data = {}
        
        # Dari structured_data jika ada
        if "structured_data" in document:
            financial_data["structured_data"] = document["structured_data"]
        
        # Dari financial_keywords_data jika ada
        if "financial_keywords_data" in document:
            financial_data["financial_keywords"] = document["financial_keywords_data"]
        
        # Metadata dokumen
        financial_data.update({
            "company_identifier": document.get("company_identifier"),
            "document_id": document.get("id"),
            "original_filename": document.get("original_filename"),
            "created_at": document.get("created_at"),
            "processing_time_seconds": document.get("processing_time_seconds", 0)
        })
        
        return financial_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving financial data: {str(e)}")
