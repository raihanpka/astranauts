import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Database sederhana menggunakan JSON file
SARANA_DATABASE_FILE = "Output/Sarana/sarana_database.json"

class SaranaDataStore:
    """Simple JSON-based data store for Sarana parsing results"""
    
    def __init__(self):
        self.db_file = SARANA_DATABASE_FILE
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        if not os.path.exists(self.db_file):
            self.save_data([])
    
    def load_data(self) -> List[Dict]:
        """Load all data from JSON file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_data(self, data: List[Dict]):
        """Save data to JSON file"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_document(self, document_data: Dict, company_identifier: str = None) -> str:
        """Add a new document and return its ID"""
        data = self.load_data()
        
        # Generate company_identifier dari nama file jika tidak disediakan
        if not company_identifier and "original_filename" in document_data:
            # Extract company name from filename (remove extension and common suffixes)
            filename = document_data["original_filename"]
            company_identifier = filename.split('.')[0].replace('_', ' ').replace('-', ' ').strip()
        
        # Generate unique ID
        doc_id = f"sarana_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(data) + 1}"
        
        # Add metadata
        document_data.update({
            "id": doc_id,
            "company_identifier": company_identifier or "unknown_company",
            "created_at": datetime.now().isoformat(),
            "module": "sarana"
        })
        
        data.append(document_data)
        self.save_data(data)
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        data = self.load_data()
        for doc in data:
            if doc.get("id") == doc_id:
                return doc
        return None
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> Dict:
        """Get all documents with pagination"""
        data = self.load_data()
        total = len(data)
        
        # Sort by created_at descending (newest first)
        sorted_data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        paginated_data = sorted_data[offset:offset + limit]
        
        return {
            "documents": paginated_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    def search_documents(self, filename: str = None, file_type: str = None) -> List[Dict]:
        """Search documents by filename or file type"""
        data = self.load_data()
        results = []
        
        for doc in data:
            match = True
            
            if filename and filename.lower() not in doc.get("original_filename", "").lower():
                match = False
            
            if file_type and doc.get("file_type", "").lower() != file_type.lower():
                match = False
            
            if match:
                results.append(doc)
        
        return results
    
    def get_documents_by_company(self, company_identifier: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get all documents for a specific company"""
        data = self.load_data()
        
        # Filter by company
        company_docs = [doc for doc in data if doc.get("company_identifier") == company_identifier]
        total = len(company_docs)
        
        # Sort by created_at descending (newest first)
        sorted_docs = sorted(company_docs, key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        paginated_docs = sorted_docs[offset:offset + limit]
        
        return {
            "documents": paginated_docs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "company_identifier": company_identifier
        }
    
    def get_latest_document_by_company(self, company_identifier: str) -> Optional[Dict]:
        """Get the most recent document for a specific company"""
        company_docs = self.get_documents_by_company(company_identifier, limit=1)
        if company_docs["documents"]:
            return company_docs["documents"][0]
        return None
    
    def get_all_companies(self) -> List[Dict]:
        """Get list of all companies with their document count"""
        data = self.load_data()
        
        companies = {}
        for doc in data:
            company_id = doc.get("company_identifier", "unknown_company")
            if company_id not in companies:
                companies[company_id] = {
                    "company_identifier": company_id,
                    "total_documents": 0,
                    "first_document": doc.get("created_at"),
                    "last_document": doc.get("created_at")
                }
            
            companies[company_id]["total_documents"] += 1
            # Update first and last document dates
            if doc.get("created_at") < companies[company_id]["first_document"]:
                companies[company_id]["first_document"] = doc.get("created_at")
            if doc.get("created_at") > companies[company_id]["last_document"]:
                companies[company_id]["last_document"] = doc.get("created_at")
        
        return list(companies.values())

# Global instance
sarana_store = SaranaDataStore()
