"""
IOC Enrichment Module
Provides threat intelligence enrichment for IOCs (IPs, domains, URLs, hashes)
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib


class IOCEnrichment:
    """Main class for IOC enrichment with multiple threat intelligence sources"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """
        Initialize enrichment with API keys
        
        Args:
            api_keys: Dictionary of API keys for various services
                     {'virustotal': 'key', 'abuseipdb': 'key', etc.}
        """
        self.api_keys = api_keys or {}
        self.cache = {}
        self.cache_ttl = timedelta(hours=24)
        self.timeout = 10
        
    def _get_cache_key(self, ioc_type: str, ioc_value: str) -> str:
        """Generate cache key for IOC"""
        return hashlib.md5(f"{ioc_type}:{ioc_value}".encode()).hexdigest()
    
    def _check_cache(self, ioc_type: str, ioc_value: str) -> Optional[Dict]:
        """Check if IOC data is cached and still valid"""
        cache_key = self._get_cache_key(ioc_type, ioc_value)
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['data']
        return None
    
    def _update_cache(self, ioc_type: str, ioc_value: str, data: Dict):
        """Update cache with enrichment data"""
        cache_key = self._get_cache_key(ioc_type, ioc_value)
        self.cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }
    
    # ==================== IP Address Enrichment ====================
    
    def enrich_ip(self, ip: str) -> Dict[str, Any]:
        """
        Enrich IP address with multiple sources
        
        Returns dict with:
            - geolocation (country, city, ISP)
            - vpn_detection (is_vpn, is_proxy, is_hosting)
            - reputation (abuse score, threat level)
            - virustotal (if available)
        """
        # Check cache first
        cached = self._check_cache('ip', ip)
        if cached:
            return cached
        
        result = {
            'ioc': ip,
            'type': 'ipv4',
            'enriched_at': datetime.now().isoformat(),
            'geolocation': self._get_ip_geolocation(ip),
            'vpn_detection': self._check_vpn(ip),
            'reputation': {},
            'virustotal': {}
        }
        
        # Add VirusTotal data if API key available
        if self.api_keys.get('virustotal'):
            result['virustotal'] = self._virustotal_ip(ip)
        
        # Add AbuseIPDB if API key available
        if self.api_keys.get('abuseipdb'):
            result['reputation'] = self._abuseipdb_check(ip)
        
        self._update_cache('ip', ip, result)
        return result
    
    def _get_ip_geolocation(self, ip: str) -> Dict:
        """Get IP geolocation using ip-api.com (free, no key required)"""
        try:
            url = f"http://ip-api.com/json/{ip}"
            params = {
                'fields': 'status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,mobile,proxy,hosting'
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'zip': data.get('zip', 'Unknown'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone', 'Unknown'),
                        'isp': data.get('isp', 'Unknown'),
                        'org': data.get('org', 'Unknown'),
                        'as': data.get('as', 'Unknown'),
                        'asname': data.get('asname', 'Unknown'),
                        'is_mobile': data.get('mobile', False),
                        'is_proxy': data.get('proxy', False),
                        'is_hosting': data.get('hosting', False)
                    }
                else:
                    return {'error': data.get('message', 'Unknown error')}
        except Exception as e:
            return {'error': str(e)}
        
        return {'error': 'Failed to retrieve geolocation'}
    
    def _check_vpn(self, ip: str) -> Dict:
        """
        Check if IP is VPN/proxy using multiple methods
        Uses vpnapi.io (free tier - 1000 requests/day, no key required)
        """
        try:
            # Try vpnapi.io first (free, no key)
            url = f"https://vpnapi.io/api/{ip}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'is_vpn': data.get('security', {}).get('vpn', False),
                    'is_proxy': data.get('security', {}).get('proxy', False),
                    'is_tor': data.get('security', {}).get('tor', False),
                    'is_relay': data.get('security', {}).get('relay', False),
                    'is_hosting': data.get('security', {}).get('hosting', False),
                    'network': data.get('network', {}).get('network', 'Unknown'),
                    'autonomous_system': data.get('network', {}).get('autonomous_system_number', 'Unknown')
                }
            
        except Exception as e:
            # Fallback to basic detection from geolocation data
            return {
                'is_vpn': False,
                'is_proxy': False,
                'is_tor': False,
                'is_hosting': False,
                'error': str(e),
                'note': 'VPN detection unavailable'
            }
        
        return {'error': 'VPN detection failed'}
    
    def _virustotal_ip(self, ip: str) -> Dict:
        """Query VirusTotal for IP reputation"""
        api_key = self.api_keys.get('virustotal')
        if not api_key:
            return {'error': 'API key not configured'}
        
        try:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
            headers = {
                'x-apikey': api_key
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'harmless': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'reputation': attributes.get('reputation', 0),
                    'country': attributes.get('country', 'Unknown'),
                    'as_owner': attributes.get('as_owner', 'Unknown'),
                    'network': attributes.get('network', 'Unknown')
                }
            elif response.status_code == 404:
                return {'error': 'IP not found in VirusTotal'}
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _abuseipdb_check(self, ip: str) -> Dict:
        """Check IP reputation on AbuseIPDB"""
        api_key = self.api_keys.get('abuseipdb')
        if not api_key:
            return {'error': 'API key not configured'}
        
        try:
            url = 'https://api.abuseipdb.com/api/v2/check'
            headers = {
                'Key': api_key,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': '90',
                'verbose': ''
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'abuse_confidence_score': data.get('abuseConfidenceScore', 0),
                    'total_reports': data.get('totalReports', 0),
                    'num_distinct_users': data.get('numDistinctUsers', 0),
                    'is_whitelisted': data.get('isWhitelisted', False),
                    'is_tor': data.get('isTor', False),
                    'country_code': data.get('countryCode', 'Unknown'),
                    'usage_type': data.get('usageType', 'Unknown')
                }
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== Hash Enrichment ====================
    
    def enrich_hash(self, hash_value: str) -> Dict[str, Any]:
        """
        Enrich file hash (MD5, SHA1, SHA256) with VirusTotal
        """
        # Check cache first
        cached = self._check_cache('hash', hash_value)
        if cached:
            return cached
        
        result = {
            'ioc': hash_value,
            'type': self._get_hash_type(hash_value),
            'enriched_at': datetime.now().isoformat(),
            'virustotal': {}
        }
        
        if self.api_keys.get('virustotal'):
            result['virustotal'] = self._virustotal_hash(hash_value)
        else:
            result['virustotal'] = {'error': 'VirusTotal API key not configured'}
        
        self._update_cache('hash', hash_value, result)
        return result
    
    def _get_hash_type(self, hash_value: str) -> str:
        """Determine hash type based on length"""
        length = len(hash_value)
        if length == 32:
            return 'md5'
        elif length == 40:
            return 'sha1'
        elif length == 64:
            return 'sha256'
        return 'unknown'
    
    def _virustotal_hash(self, hash_value: str) -> Dict:
        """Query VirusTotal for file hash"""
        api_key = self.api_keys.get('virustotal')
        if not api_key:
            return {'error': 'API key not configured'}
        
        try:
            url = f"https://www.virustotal.com/api/v3/files/{hash_value}"
            headers = {
                'x-apikey': api_key
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'harmless': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'file_type': attributes.get('type_description', 'Unknown'),
                    'file_size': attributes.get('size', 0),
                    'names': attributes.get('names', [])[:5],  # First 5 names
                    'reputation': attributes.get('reputation', 0),
                    'popular_threat_classification': attributes.get('popular_threat_classification', {})
                }
            elif response.status_code == 404:
                return {'error': 'Hash not found in VirusTotal'}
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== Domain/URL Enrichment ====================
    
    def enrich_domain(self, domain: str) -> Dict[str, Any]:
        """
        Enrich domain with VirusTotal and other sources
        """
        # Check cache first
        cached = self._check_cache('domain', domain)
        if cached:
            return cached
        
        result = {
            'ioc': domain,
            'type': 'domain',
            'enriched_at': datetime.now().isoformat(),
            'virustotal': {}
        }
        
        if self.api_keys.get('virustotal'):
            result['virustotal'] = self._virustotal_domain(domain)
        else:
            result['virustotal'] = {'error': 'VirusTotal API key not configured'}
        
        self._update_cache('domain', domain, result)
        return result
    
    def _virustotal_domain(self, domain: str) -> Dict:
        """Query VirusTotal for domain reputation"""
        api_key = self.api_keys.get('virustotal')
        if not api_key:
            return {'error': 'API key not configured'}
        
        try:
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"
            headers = {
                'x-apikey': api_key
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'harmless': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'reputation': attributes.get('reputation', 0),
                    'categories': attributes.get('categories', {}),
                    'creation_date': attributes.get('creation_date'),
                    'last_analysis_date': attributes.get('last_analysis_date')
                }
            elif response.status_code == 404:
                return {'error': 'Domain not found in VirusTotal'}
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def enrich_url(self, url: str) -> Dict[str, Any]:
        """
        Enrich URL with VirusTotal
        """
        # Check cache first
        cached = self._check_cache('url', url)
        if cached:
            return cached
        
        result = {
            'ioc': url,
            'type': 'url',
            'enriched_at': datetime.now().isoformat(),
            'virustotal': {}
        }
        
        if self.api_keys.get('virustotal'):
            result['virustotal'] = self._virustotal_url(url)
        else:
            result['virustotal'] = {'error': 'VirusTotal API key not configured'}
        
        self._update_cache('url', url, result)
        return result
    
    def _virustotal_url(self, url: str) -> Dict:
        """Query VirusTotal for URL reputation"""
        api_key = self.api_keys.get('virustotal')
        if not api_key:
            return {'error': 'API key not configured'}
        
        try:
            # First, get the URL ID
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            
            vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            headers = {
                'x-apikey': api_key
            }
            
            response = requests.get(vt_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'harmless': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'reputation': attributes.get('reputation', 0),
                    'categories': attributes.get('categories', {}),
                    'last_analysis_date': attributes.get('last_analysis_date')
                }
            elif response.status_code == 404:
                # URL not scanned yet, submit it
                return {'error': 'URL not found in VirusTotal (consider submitting for analysis)'}
            elif response.status_code == 401:
                return {'error': 'Invalid API key'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== Batch Enrichment ====================
    
    def enrich_iocs_batch(self, iocs: Dict[str, List[str]], 
                          progress_callback=None) -> Dict[str, List[Dict]]:
        """
        Enrich multiple IOCs with rate limiting
        
        Args:
            iocs: Dictionary of IOC types and values
                  {'ipv4': ['1.2.3.4', ...], 'hash_md5': [...], ...}
            progress_callback: Optional callback function(current, total, message)
        
        Returns:
            Dictionary with enrichment results per IOC type
        """
        results = {}
        total = sum(len(values) for values in iocs.values())
        current = 0
        
        # Process IPs
        if 'ipv4' in iocs:
            results['ipv4'] = []
            for ip in iocs['ipv4']:
                if progress_callback:
                    progress_callback(current, total, f"Enriching IP: {ip}")
                results['ipv4'].append(self.enrich_ip(ip))
                current += 1
                time.sleep(0.25)  # Rate limiting
        
        # Process hashes
        for hash_type in ['hash_md5', 'hash_sha1', 'hash_sha256']:
            if hash_type in iocs:
                results[hash_type] = []
                for hash_val in iocs[hash_type]:
                    if progress_callback:
                        progress_callback(current, total, f"Enriching hash: {hash_val[:16]}...")
                    results[hash_type].append(self.enrich_hash(hash_val))
                    current += 1
                    time.sleep(0.25)  # Rate limiting
        
        # Process domains
        if 'domain' in iocs:
            results['domain'] = []
            for domain in iocs['domain']:
                if progress_callback:
                    progress_callback(current, total, f"Enriching domain: {domain}")
                results['domain'].append(self.enrich_domain(domain))
                current += 1
                time.sleep(0.25)  # Rate limiting
        
        # Process URLs
        if 'url' in iocs:
            results['url'] = []
            for url in iocs['url']:
                if progress_callback:
                    progress_callback(current, total, f"Enriching URL: {url[:50]}...")
                results['url'].append(self.enrich_url(url))
                current += 1
                time.sleep(0.25)  # Rate limiting
        
        if progress_callback:
            progress_callback(total, total, "Enrichment complete!")
        
        return results
