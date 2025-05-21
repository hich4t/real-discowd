import asyncio, aiofiles
import aiohttp
import json
import re
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from selectolax.parser import HTMLParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cooltext_api")

@dataclass
class BaseItem:
    """Base class for CoolText items"""
    name: str
    preview: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class Style(BaseItem):
    """Represents a CoolText logo style"""
    id: int = None
    input_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.input_fields is None:
            self.input_fields = {}

@dataclass
class Font(BaseItem):
    """Represents a CoolText font"""
    character_map: str = None
    
    def to_dict(self):
        return asdict(self)


class CoolTextAPI:
    """Asynchronous API client for CoolText.com"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.base_url = "https://cooltext.com"
        self.cdn_url = "https://ct.mob0.com"
        
        self.styles: List[Style] = []
        self.fonts: List[Font] = []
        
        # Tag categories
        self.style_tags = ["Animated", "Black", "Blue", "Brown", "Burning", "Casual", "Chrome", 
                          "Classic", "Distressed", "Elegant", "Fire", "Fun", "Girly", "Glossy", 
                          "Glowing", "Gold", "Gradient", "Gray", "Green", "Heavy", "Holiday", 
                          "Ice", "Medieval", "Metal", "Neon", "Orange", "Outline", "Pink", 
                          "Purple", "Red", "Retro", "Rounded", "Science-Fiction", "Script", 
                          "Shadow", "Sharp", "Shiny", "Space", "Sparkle", "Stencil", "Stone", 
                          "Trippy", "Valentines", "White", "Yellow"]
        
        self.font_tags = ["3D", "Aggressive", "All Caps", "Ancient", "Arab", "Asian", "Black", 
                         "Block", "Blood", "Bold", "Brand", "Brandname", "Brush", "Bubbly", 
                         "Calligraphy", "Cartoon", "Christmas", "Classic", "Clean", "Comic", 
                         "Condensed", "Cool", "Curly", "Cursive", "Curvy", "Cute", "Dark", 
                         "Decorative", "Dingbats", "Dingfonts", "Distressed", "Dot Matrix", 
                         "Dripping", "Drug", "Elegant", "Famous", "Fancy", "Fantasy", "Fast", 
                         "Festive", "Flaming", "Flourish", "Flowers", "Foreign", "Freaky", 
                         "Fun", "Futuristic", "Games", "Girly", "Gothic", "Graffiti", "Grunge", 
                         "Handwriting", "Hard to read", "Hearts", "Heavy", "Holiday", "Horror", 
                         "Huge", "Industrial", "Initials", "International", "Italic", "Jumbled", 
                         "Kids", "Korean", "Love", "Lovely", "Lowercase", "Magic", "Medieval", 
                         "Modern", "Monospace", "Movies and TV", "Music", "Mystery", "Old", 
                         "Outline", "Pirate", "Pixel", "Pixel or Small", "Plain", "Retro", 
                         "Rich", "Romantic", "Rounded", "Sans Serif", "Science-Fiction", 
                         "Scratched", "Script", "Script or Brush", "Serif", "Sharp", "Slab", 
                         "Slab Serif", "Slanted", "Small Caps", "Spiked", "Stars", "Stencil", 
                         "Street", "Stylish", "Tall", "Technical", "Techno", "Thick", "Thin", 
                         "Traditional", "Tribal", "Typewriter", "Unicode Arabic", 
                         "Unicode Chinese", "Unicode Japanese", "Unicode Korean", "Violent", 
                         "Wide", "Woodcut"]
        
        self.alphabetic_tags = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        self._session = session
        self._externally_managed_session = session is not None
        
    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={"User-Agent": "CoolTextAPIWrapper/1.0"})
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._externally_managed_session and self._session is not None:
            await self._session.close()
            self._session = None
    
    async def _ensure_session(self):
        """Ensure we have an active session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={"User-Agent": "CoolTextAPIWrapper/1.0"})
            self._externally_managed_session = False
    
    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL"""
        await self._ensure_session()
        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Got status {response.status} for URL: {url}")
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    async def initialize(self) -> None:
        """Initialize the API by fetching styles and fonts"""
        await self._ensure_session()
        
        # Fetch basic styles first
        logger.info("Fetching basic styles...")
        self.styles = await self.fetch_styles()
        
        # Create a dictionary for easier lookup and tag addition
        styles_dict = {style.name: style for style in self.styles}
        
        # Fetch styles with tags
        logger.info("Fetching style tags...")
        style_tags_tasks = [self.fetch_styles(tag=tag) for tag in self.style_tags]
        styles_with_tags = await asyncio.gather(*style_tags_tasks)
        
        # Add tags to the styles
        for i, styles_tag_group in enumerate(styles_with_tags):
            for style in styles_tag_group:
                if style.name in styles_dict:
                    styles_dict[style.name].tags.append(self.style_tags[i])
        
        # Update the styles list
        self.styles = list(styles_dict.values())
        
        # Fetch fonts
        logger.info("Fetching fonts...")
        fonts_dict = {}
        
        # Fetch fonts by alphabetic tag
        fonts_alpha_tasks = [self.fetch_fonts(tag=tag) for tag in self.alphabetic_tags]
        fonts_alpha_results = await asyncio.gather(*fonts_alpha_tasks)
        
        for font_group in fonts_alpha_results:
            for font in font_group:
                fonts_dict[font.name] = font
        
        # Fetch fonts by category tag
        logger.info("Fetching font tags...")
        fonts_tags_tasks = [self.fetch_fonts(tag=tag) for tag in self.font_tags]
        fonts_tags_results = await asyncio.gather(*fonts_tags_tasks)
        
        for i, font_group in enumerate(fonts_tags_results):
            for font in font_group:
                if font.name in fonts_dict:
                    fonts_dict[font.name].tags.append(self.font_tags[i])
        
        # Update the fonts list
        self.fonts = list(fonts_dict.values())
        
        # Fetch details for each style
        logger.info("Fetching style details...")
        for style in self.styles:
            if style.id:
                await self.fetch_style_details(style)
        
        logger.info(f"Initialization complete. Found {len(self.styles)} styles and {len(self.fonts)} fonts.")
    
    async def fetch_styles(self, sort: str = "", tag: str = "") -> List[Style]:
        """Fetch logo styles from CoolText"""
        url_suffix = f"Logos{f'-{tag}' if tag else ''}{'?Alphabetized=1' if sort else ''}"
        url = f"{self.base_url}/{url_suffix}"
        
        html = await self._fetch_html(url)
        if not html:
            return []
        
        styles = []
        tree = HTMLParser(html)
        
        # Find the div containing the styles
        div = tree.css_first("body > table > tbody > tr:nth-child(2) > td.Center > div")
        if not div:
            logger.warning(f"Could not find styles div in {url}")
            return []
        
        # Extract style information from each link
        for a in div.css("a"):
            img = a.css_first("img")
            if not img:
                continue
                
            href = a.attributes.get("href", "")
            
            # Extract name from href
            name = href.split("-")[-1] if href else None
            if not name:
                continue
            
            # Extract ID from onmouseover attribute
            onmouseover = a.attributes.get("onmouseover", "")
            id_match = re.search(r"Tip\(event, this, '(\d+)\.(?:png|gif)'\)", onmouseover)
            style_id = int(id_match.group(1)) if id_match else None
            
            # Get preview image URL
            preview = img.attributes.get("src", "")
            if preview and not preview.startswith(("http:", "https:")):
                preview = f"{self.cdn_url}/{preview}" if not preview.startswith("/") else f"{self.base_url}{preview}"
            
            styles.append(Style(name=name, id=style_id, preview=preview))
        
        return styles
    
    async def fetch_fonts(self, sort: str = "", tag: str = "") -> List[Font]:
        """Fetch fonts from CoolText"""
        url_suffix = f"Fonts{f'-{tag}' if tag else ''}{'?Alphabetized=1' if sort else ''}"
        url = f"{self.base_url}/{url_suffix}"
        
        html = await self._fetch_html(url)
        if not html:
            return []
        
        fonts = []
        tree = HTMLParser(html)
        
        # Find the td containing the fonts
        td = tree.css_first("body > table > tbody > tr:nth-child(2) > td:nth-child(2)")
        if not td:
            logger.warning(f"Could not find fonts td in {url}")
            return []
        
        # Extract font information from each link
        for a in td.css("a"):
            img = a.css_first("img")
            if not img:
                continue
            
            # Get preview image URL
            preview = img.attributes.get("src", "")
            if preview and not preview.startswith(("http:", "https:")):
                preview = f"{self.cdn_url}/{preview}" if not preview.startswith("/") else f"{self.base_url}{preview}"
            
            # Extract font name from onmouseover attribute
            onmouseover = a.attributes.get("onmouseover", "")
            name_match = re.search(r"Tip\(event, this, '(?:\.\./Fonts/CharacterMap/)?(.+?)'\)", onmouseover)
            name = name_match.group(1) if name_match else None
            
            if not name:
                continue
            
            # Create character map URL
            character_map = f'{self.cdn_url}/Fonts/CharacterMap/{name}.png'
            
            fonts.append(Font(name=name, character_map=character_map, preview=preview))
        
        return fonts
    
    async def fetch_style_details(self, style: Style) -> None:
        """Fetch detailed information about a style, including input fields"""
        if not style.id:
            logger.warning(f"Cannot fetch details for style {style.name}: no ID")
            return
        
        url = f"{self.base_url}/Logo-Design-{style.name.replace(' ', '-')}"
        html = await self._fetch_html(url)
        if not html:
            return
        
        tree = HTMLParser(html)
        
        # Extract input fields
        input_fields = {}
        
        # Find form elements
        # Search for the text input field first (usually with name="Text")
        text_input = tree.css_first("input[name='Text']")
        if text_input:
            input_fields["Text"] = {
                "value": text_input.attributes.get("value", ""),
                "type": text_input.attributes.get("type", "text")
            }
        
        # Get all other form elements
        form = tree.css_first("form")
        if form:
            # Get the hidden inputs for default values
            for input_elem in form.css("input[type=hidden]"):
                name = input_elem.attributes.get("name")
                value = input_elem.attributes.get("value", "")
                if name and name != "Text":  # Skip "Text" as we've already handled it
                    input_fields[name] = value
            
            # Get visible inputs
            for input_elem in form.css("input:not([type=hidden])"):
                name = input_elem.attributes.get("name")
                value = input_elem.attributes.get("value", "")
                type_attr = input_elem.attributes.get("type", "text")
                
                if name and name != "Text":  # Skip "Text" as we've already handled it
                    input_fields[name] = {
                        "value": value,
                        "type": type_attr
                    }
            
            # Get select elements
            for select_elem in form.css("select"):
                name = select_elem.attributes.get("name")
                if name:
                    options = []
                    selected_value = None
                    
                    for option in select_elem.css("option"):
                        value = option.attributes.get("value", "")
                        text = option.text()
                        selected = "selected" in option.attributes
                        
                        options.append({
                            "value": value,
                            "text": text,
                            "selected": selected
                        })
                        
                        if selected:
                            selected_value = value
                    
                    input_fields[name] = {
                        "type": "select",
                        "options": options,
                        "value": selected_value
                    }
        
        # Update the style with the input fields
        style.input_fields = input_fields
    
    async def generate_logo(self, style_id: int, text: str, **params) -> str:
        """Generate a logo using the specified style and parameters
        
        Args:
            style_id: The ID of the style to use
            text: The text to use in the logo
            **params: Additional parameters to customize the logo
            
        Returns:
            str: URL of the generated logo image
        """
        await self._ensure_session()
        
        # Base parameters - ensure "Text" is correctly formatted
        data = {
            "LogoID": style_id,
            "Text": text  # Keep the full text as is
        }
        
        # Add custom parameters
        data.update(params)
        
        # Log the request parameters for debugging
        logger.debug(f"Generating logo with parameters: {data}")
        
        url = f"{self.base_url}/GenerateLogojson"
        
        try:
            # Make sure to send the right content type for form data
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{self.base_url}/GenLogo?LogoID={style_id}"
            }
            
            async with self._session.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Error generating logo: HTTP {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text[:200]}...")
                    return None
                
                result = await response.json()
                image_url = result.get("imageUrl")
                
                # Ensure the URL is absolute
                if image_url and not image_url.startswith(("http:", "https:")):
                    image_url = f"{self.cdn_url}/{image_url}" if not image_url.startswith("/") else f"{self.base_url}{image_url}"
                
                return image_url
        except Exception as e:
            logger.error(f"Error generating logo: {e}")
            return None
    
    async def download_logo(self, url: str, filename: str) -> bool:
        """Download a logo image
        
        Args:
            url: The URL of the logo image
            filename: The local filename to save the image as
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not url:
            return False
            
        await self._ensure_session()
        
        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error downloading logo: {response.status}")
                    return False
                
                async with aiofiles.open(filename, "wb") as f:
                    await f.write(await response.read())
                
                return True
        except Exception as e:
            logger.error(f"Error downloading logo: {e}")
            return False
    
    def get_style_by_id(self, style_id: int) -> Optional[Style]:
        """Get a style by its ID"""
        for style in self.styles:
            if style.id == style_id:
                return style
        return None
    
    def get_style_by_name(self, name: str) -> Optional[Style]:
        """Get a style by its name"""
        for style in self.styles:
            if style.name.lower() == name.lower():
                return style
        return None
    
    def get_font_by_name(self, name: str) -> Optional[Font]:
        """Get a font by its name"""
        for font in self.fonts:
            if font.name.lower() == name.lower():
                return font
        return None
    
    def search_styles(self, query: str) -> List[Style]:
        """Search for styles by name or tag"""
        query = query.lower()
        results = []
        
        for style in self.styles:
            if query in style.name.lower():
                results.append(style)
                continue
                
            for tag in style.tags:
                if query in tag.lower():
                    results.append(style)
                    break
        
        return results
    
    def search_fonts(self, query: str) -> List[Font]:
        """Search for fonts by name or tag"""
        query = query.lower()
        results = []
        
        for font in self.fonts:
            if query in font.name.lower():
                results.append(font)
                continue
                
            for tag in font.tags:
                if query in tag.lower():
                    results.append(font)
                    break
        
        return results
    
    def export_styles(self, filename: str) -> None:
        """Export styles to a JSON file"""
        with open(filename, "w") as f:
            json.dump([asdict(style) for style in self.styles], f, indent=2)
    
    def export_fonts(self, filename: str) -> None:
        """Export fonts to a JSON file"""
        with open(filename, "w") as f:
            json.dump([asdict(font) for font in self.fonts], f, indent=2)