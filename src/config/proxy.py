from dataclasses import dataclass
from typing import Optional, Dict
import requests
import logging

@dataclass
class ProxyConfig:
    enabled: bool = False
    http: Optional[str] = None
    https: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        if not self.enabled:
            return {}
            
        proxies = {}
        if self.http:
            proxies['http'] = self._format_proxy_url('http')
        if self.https:
            proxies['https'] = self._format_proxy_url('https')
        return proxies
    
    def _format_proxy_url(self, protocol: str) -> str:
        proxy_url = getattr(self, protocol)
        if self.username and self.password:
            proxy_url = proxy_url.replace('://', f'://{self.username}:{self.password}@')
        return proxy_url

class ProxyManager:
    def __init__(self):
        self.config = ProxyConfig()
        self.session: Optional[requests.Session] = None
    
    def configure(self, config: ProxyConfig):
        self.config = config
        self._setup_session()
    
    def _setup_session(self):
        self.session = requests.Session()
        if self.config.enabled:
            self.session.proxies = self.config.to_dict()
            logging.info(f"プロキシを設定: {self.session.proxies}")
    
    def get_session(self) -> requests.Session:
        if self.session is None:
            self._setup_session()
        return self.session