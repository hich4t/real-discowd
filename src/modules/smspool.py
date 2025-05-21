"""
SMSPool Async Library

A Python async library for interacting with the SMSPool service.
This library provides an async interface for obtaining phone numbers
and retrieving SMS messages from the SMSPool service.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Union, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SMSPoolError(Exception):
    """Base exception for all SMSPool errors."""
    pass

class AuthError(SMSPoolError):
    """Authentication error with SMSPool API."""
    pass

class RequestError(SMSPoolError):
    """Error during request to SMSPool API."""
    pass

class Entity:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class Country(Entity):
    def __init__(self, id: int, name: str, short_name: str, region: str = ""):
        super().__init__(id, name)
        self.short_name = short_name
        self.region = region

class Service(Entity):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

class Pool(Entity):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

class Rates:
    def __init__(self, country_id, name, short_name, price, low_price, success_rate, stock):
        self.country = Country(country_id, name, short_name, None)
        self.price = price
        self.low_price = low_price
        self.success_rate = success_rate
        self.stock = stock

class Phone:
    def __init__(self, number, cc, phonenumber, orderid, country, service, pool, expires_in, expiration, message, cost, cost_in_cents, current_balance):
        self.number = number
        self.cc = cc
        self.phonenumber = phonenumber
        self.orderid = orderid
        self.country = country
        self.service = service
        self.pool = pool
        self.expires_in = expires_in
        self.expiration = expiration
        self.message = message
        self.cost = float(cost)
        self.cost_in_cents = cost_in_cents
        self.current_balance = float(current_balance)

class Response:
    def __init__(self, success, message: str = None):
        self.success = success
        self.message = message

class Check(Response):
    def __init__(self, success, sms: str = None, full_sms: str = None):
        super().__init__(success)
        self.sms = sms
        self.full_sms = full_sms

class Resend(Response):
    def __init__(self, success, resends, resendCost):
        super().__init__(success)
        self.success = success
        self.resends = resends
        self.resendCost = resendCost

class Cancel(Response):
    def __init__(self, success, message):
        super().__init__(success, message)

class SMSPoolClient:
    """Async client for the SMSPool API."""
    
    BASE_URL = "https://api.smspool.net/"
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the SMSPool client.
        
        Args:
            api_key: Your SMSPool API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = None
        self.services = []
        self.countries = []
        self.pools = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            self.services, self.countries, self.pools = await asyncio.gather(*[self.get_services(), self.get_countries(), self.get_pools()])
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _ensure_session(self):
        """Ensure an active aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            self.services, self.countries, self.pools = await asyncio.gather(*[self.get_services(), self.get_countries(), self.get_pools()])
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = {}) -> Dict:
        """
        Make an async request to the SMSPool API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
        
        Raises:
            AuthError: When authentication fails
            RequestError: When request fails
        """
        await self._ensure_session()
        
        url = f"{self.BASE_URL}/{endpoint}"

        self.session.headers["Accept"] = "application/json"

        formData = aiohttp.FormData()
        formData.add_field("key", self.api_key)
        for key,value in params.items():
            formData.add_field(key,value)

        try:
            if method.upper() == "GET":
                async with self.session.get(url, data=formData) as response:
                    response_data = await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, data=formData) as response:
                    response_data = await response.json()
            else:
                raise RequestError(f"Unsupported HTTP method: {method}")
            
            if response.status == 401:
                raise AuthError("Authentication failed. Check your API key.")
            
            if response.status != 200:
                error_msg = response_data
                print(f"Request failed: {error_msg} {response.status}")
                #raise RequestError(f"Request failed: {error_msg} {response.status}")
            
            return response_data
            
        except aiohttp.ClientError as e:
            raise RequestError(f"Request failed: {str(e)}")
    
    async def get_services(self) -> List[Service]:
        """
        Get available services.
        
        Returns:
            List of available services
        """
        response = await self._make_request("GET", "service/retrieve_all")
        print(response)
        return [Service(service["ID"], service["name"]) for service in response]
    
    def get_service(self, name: str = None, id: int = None) -> Service:
        for service in self.services:
            if service.name.lower() == name.lower() or service.id == id:
                return service
        
        return None

    async def get_countries(self) -> List[Country]:
        """
        Get available countries.
        
        Returns:
            List of available countries
        """
        response = await self._make_request("GET", "country/retrieve_all")
        print(response) 
        return [Country(country["ID"], country["name"], country["short_name"], country["region"]) for country in response]
    
    def get_country(self, name: str = None, id: int = None) -> Country:
        for country in self.countries:
            if country.name.lower() == name.lower() or country.id == id:
                return country
        
        return None

    async def get_pools(self) -> List[Pool]:
        """
        Get available pools.
        
        Returns:
            List of available pools
        """
        response = await self._make_request("GET", "pool/retrieve_all")
        print(response)
        return [Pool(pool["ID"], pool["name"]) for pool in response]
    
    async def get_balance(self) -> float:
        """
        Get account balance.
        
        Returns:
            Account balance as float
        """
        response = await self._make_request("POST", "request/balance")
        print(response)
        return float(response.get("balance", 0))

    async def retrieve_success_rate(self, service, sort_by: int = 0, no_stock: bool = 0) -> List[Rates]:
        """
        Retrieve success rates of service.
        
        Returns:
            List of success rates
        """
        response = await self._make_request("POST", "request/success_rate", {"service": service})
        print(response)
        rates = [Rates(data["country_id"], data["name"], data["short_name"], data["price"], data["low_price"], data["success_rate"], data["stock"]) for data in response]
        if sort_by == 1:
            rates = sorted(rates, key=lambda r: r.low_price)
        elif sort_by == 2:
            rates = sorted(rates, key=lambda r: r.price)
        if no_stock:
            rates = [rate for rate in rates if rate.stock > 0]
        return rates
    
    async def order_sms(self, service: int, country: int, pricing_option) -> Phone:
        """
        Order one time sms for service.
        
        Returns:
            List of success rates
        """
        response = await self._make_request("POST", "purchase/sms", {"service": service, "country": country, "pricing_option": pricing_option})
        print(response)
        return Phone(response["number"], response["cc"], response["phonenumber"], response["orderid"], response["country"], response["service"], response["pool"], response["expires_in"], response["expiration"], response["message"], response["cost"], response["cost_in_cents"], response["current_balance"])
    
    async def check_sms(self, order_id) -> Check:
        """
        Checks sms by order_id
        
        Returns:
            uhh
        """
        response = await self._make_request("POST", "sms/check", {"orderid": order_id})
        print(response)
        return Check(response.get("success"), response.get("sms", None), response.get("sms_full", None))

    async def resend_sms(self, order_id) -> Resend:
        """
        Resends sms if possible.
        
        Returns:
            Success or nah
        """
        response = await self._make_request("POST", "sms/resend", {"orderid": order_id})
        print(response)
        return Resend(response["success"], response["resends"], response["resendCost"]) 

    async def cancel_sms(self, order_id) -> Cancel:
        """
        Cancel sms order if possible.
        
        Returns:
            Success or nah
        """
        response = await self._make_request("POST", "sms/cancel", {"orderid": order_id})
        print(response)
        return Cancel(response["success"], response.get("message", "Something went wrong"))
    