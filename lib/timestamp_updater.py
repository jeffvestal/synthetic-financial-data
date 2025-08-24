"""
Timestamp Updater for Synthetic Financial Data

Updates timestamps in Elasticsearch documents or data files to current time or with offset.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch


class TimestampUpdater:
    """Handles timestamp updates for financial data."""
    
    # Define timestamp fields for each index type
    TIMESTAMP_FIELDS = {
        'financial_accounts': ['last_updated'],
        'financial_holdings': ['last_updated', 'purchase_date'],
        'financial_asset_details': ['last_updated', 'current_price.last_updated'],
        'financial_news': ['last_updated', 'published_date'],
        'financial_reports': ['last_updated', 'published_date']
    }
    
    @staticmethod
    def calculate_target_timestamp(offset_hours: int = 0) -> str:
        """
        Calculate target timestamp with optional offset.
        
        Args:
            offset_hours: Hours to offset from now (negative for past)
            
        Returns:
            ISO format timestamp string
        """
        target_time = datetime.now() + timedelta(hours=offset_hours)
        return target_time.isoformat(timespec='seconds')
    
    @classmethod
    def update_elasticsearch_index(cls, es_client: Elasticsearch, index_name: str, 
                                 offset_hours: int = 0, dry_run: bool = False) -> Dict[str, Any]:
        """
        Update all timestamps in a specific Elasticsearch index.
        
        Args:
            es_client: Elasticsearch client
            index_name: Name of index to update
            offset_hours: Hours offset from current time
            dry_run: If True, show what would be updated without making changes
            
        Returns:
            Dict with update statistics
        """
        target_timestamp = cls.calculate_target_timestamp(offset_hours)
        
        # Get the timestamp fields for this index
        fields = cls.TIMESTAMP_FIELDS.get(index_name, ['last_updated'])
        
        # Build the update script
        script_lines = []
        for field in fields:
            if '.' in field:  # Handle nested fields
                parts = field.split('.')
                script_lines.append(f"if (ctx._source.{parts[0]} != null) {{ ctx._source.{field} = params.timestamp; }}")
            else:
                script_lines.append(f"if (ctx._source.containsKey('{field}')) {{ ctx._source.{field} = params.timestamp; }}")
        
        update_body = {
            "script": {
                "source": " ".join(script_lines),
                "params": {
                    "timestamp": target_timestamp
                }
            }
        }
        
        if dry_run:
            # Just count documents that would be updated
            count_response = es_client.count(index=index_name)
            return {
                'index': index_name,
                'dry_run': True,
                'would_update': count_response['count'],
                'target_timestamp': target_timestamp,
                'fields': fields
            }
        
        # Execute the update
        response = es_client.update_by_query(
            index=index_name,
            body=update_body,
            refresh=True,
            conflicts='proceed'
        )
        
        return {
            'index': index_name,
            'updated': response['updated'],
            'total': response['total'],
            'failures': response.get('failures', []),
            'target_timestamp': target_timestamp,
            'fields': fields
        }
    
    @classmethod
    def update_all_indices(cls, es_client: Elasticsearch, offset_hours: int = 0, 
                          dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Update timestamps in all financial indices.
        
        Args:
            es_client: Elasticsearch client
            offset_hours: Hours offset from current time
            dry_run: If True, show what would be updated without making changes
            
        Returns:
            List of update results for each index
        """
        results = []
        
        for index_name in cls.TIMESTAMP_FIELDS.keys():
            # Check if index exists
            if es_client.indices.exists(index=index_name):
                result = cls.update_elasticsearch_index(
                    es_client, index_name, offset_hours, dry_run
                )
                results.append(result)
            else:
                results.append({
                    'index': index_name,
                    'error': 'Index does not exist'
                })
        
        return results
    
    @classmethod
    def update_document_timestamps(cls, document: Dict[str, Any], 
                                  doc_type: str, offset_hours: int = 0) -> Dict[str, Any]:
        """
        Update timestamps in a single document (for in-flight updates).
        
        Args:
            document: Document to update
            doc_type: Type of document (accounts, holdings, news, etc.)
            offset_hours: Hours offset from current time
            
        Returns:
            Updated document
        """
        target_timestamp = cls.calculate_target_timestamp(offset_hours)
        
        # Map doc types to index names
        type_to_index = {
            'accounts': 'financial_accounts',
            'holdings': 'financial_holdings',
            'asset_details': 'financial_asset_details',
            'news': 'financial_news',
            'reports': 'financial_reports'
        }
        
        index_name = type_to_index.get(doc_type)
        if not index_name:
            return document
        
        fields = cls.TIMESTAMP_FIELDS.get(index_name, ['last_updated'])
        
        # Update each timestamp field
        for field in fields:
            if '.' in field:  # Handle nested fields
                parts = field.split('.')
                if parts[0] in document and isinstance(document[parts[0]], dict):
                    if len(parts) == 2:
                        document[parts[0]][parts[1]] = target_timestamp
            else:
                if field in document:
                    document[field] = target_timestamp
        
        return document
    
    @classmethod
    def update_file_timestamps(cls, filepath: str, output_filepath: str = None,
                             doc_type: str = None, offset_hours: int = 0) -> int:
        """
        Update timestamps in a JSONL file.
        
        Args:
            filepath: Path to input JSONL file
            output_filepath: Path to output file (if None, updates in place)
            doc_type: Type of documents in file
            offset_hours: Hours offset from current time
            
        Returns:
            Number of documents updated
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Infer doc type from filename if not provided
        if not doc_type:
            filename = os.path.basename(filepath).lower()
            if 'accounts' in filename:
                doc_type = 'accounts'
            elif 'holdings' in filename:
                doc_type = 'holdings'
            elif 'asset' in filename:
                doc_type = 'asset_details'
            elif 'news' in filename:
                doc_type = 'news'
            elif 'report' in filename:
                doc_type = 'reports'
            else:
                doc_type = 'unknown'
        
        # If no output file specified, create a temp file
        if output_filepath is None:
            output_filepath = filepath + '.tmp'
            replace_original = True
        else:
            replace_original = False
        
        count = 0
        with open(filepath, 'r') as infile, open(output_filepath, 'w') as outfile:
            for line in infile:
                if line.strip():
                    doc = json.loads(line)
                    updated_doc = cls.update_document_timestamps(doc, doc_type, offset_hours)
                    outfile.write(json.dumps(updated_doc) + '\n')
                    count += 1
        
        # Replace original file if needed
        if replace_original:
            os.replace(output_filepath, filepath)
        
        return count
    
    @classmethod
    def format_results(cls, results: List[Dict[str, Any]]) -> str:
        """
        Format update results for display.
        
        Args:
            results: List of update results
            
        Returns:
            Formatted string for display
        """
        lines = []
        total_updated = 0
        
        for result in results:
            if 'error' in result:
                lines.append(f"❌ {result['index']}: {result['error']}")
            elif result.get('dry_run'):
                lines.append(f"🔍 {result['index']}: Would update {result['would_update']} documents")
                lines.append(f"   Fields: {', '.join(result['fields'])}")
            else:
                lines.append(f"✓ {result['index']}: Updated {result['updated']}/{result['total']} documents")
                total_updated += result['updated']
                if result.get('failures'):
                    lines.append(f"   ⚠️ {len(result['failures'])} failures")
        
        if not any(r.get('dry_run') for r in results):
            lines.append(f"\n📊 Total: {total_updated} documents updated")
        
        return '\n'.join(lines)