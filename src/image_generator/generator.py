"""
Image generator for blog thumbnails and banners
"""
import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from loguru import logger
from pathlib import Path
from config.settings import settings

class ImageGenerator:
    """Generates thumbnails and banner images for blog posts"""
    
    def __init__(self):
        self.static_path = settings.static_path
        self.static_path.mkdir(parents=True, exist_ok=True)
        
        # Default colors for Re-Defined brand
        self.brand_colors = {
            'primary': '#2E86AB',  # Blue
            'secondary': '#A23B72',  # Purple
            'accent': '#F18F01',   # Orange
            'dark': '#1A1A2E',     # Dark blue
            'light': '#FFFFFF'     # White
        }
        
    def generate_thumbnail(
        self,
        title: str,
        subtitle: Optional[str] = None,
        style: str = "modern"
    ) -> str:
        """
        Generate a thumbnail image for a blog post
        
        Args:
            title: Blog post title
            subtitle: Optional subtitle
            style: Visual style (modern, minimal, gradient)
            
        Returns:
            Path to the generated thumbnail
        """
        # Image dimensions for thumbnail
        width, height = 1200, 630  # Standard social media size
        
        # Create base image
        img = self._create_base_image(width, height, style)
        draw = ImageDraw.Draw(img)
        
        # Add text
        self._add_text_to_image(draw, title, subtitle, width, height)
        
        # Add Re-Defined logo/branding
        self._add_branding(img, draw)
        
        # Save image
        filename = f"thumbnail_{self._generate_filename(title)}.png"
        filepath = self.static_path / filename
        img.save(filepath, 'PNG', quality=95)
        
        logger.info(f"Generated thumbnail: {filepath}")
        return str(filepath)
    
    def generate_banner(
        self,
        title: str,
        category: Optional[str] = None,
        style: str = "modern"
    ) -> str:
        """
        Generate a banner image for a blog post
        
        Args:
            title: Blog post title
            category: Blog category
            style: Visual style
            
        Returns:
            Path to the generated banner
        """
        # Banner dimensions
        width, height = 1920, 600
        
        # Create base image
        img = self._create_base_image(width, height, style)
        draw = ImageDraw.Draw(img)
        
        # Add text with different layout for banner
        self._add_banner_text(draw, title, category, width, height)
        
        # Add design elements
        self._add_design_elements(img, draw, style)
        
        # Save image
        filename = f"banner_{self._generate_filename(title)}.png"
        filepath = self.static_path / filename
        img.save(filepath, 'PNG', quality=95)
        
        logger.info(f"Generated banner: {filepath}")
        return str(filepath)
    
    def generate_with_ai(
        self,
        prompt: str,
        image_type: str = "thumbnail"
    ) -> Optional[str]:
        """
        Generate image using AI (DALL-E or Stable Diffusion)
        
        Args:
            prompt: Text prompt for image generation
            image_type: Type of image (thumbnail or banner)
            
        Returns:
            Path to generated image or None if failed
        """
        if settings.dalle_api_key:
            return self._generate_dalle_image(prompt, image_type)
        elif settings.stability_api_key:
            return self._generate_stability_image(prompt, image_type)
        else:
            logger.warning("No AI image generation API configured")
            return None
    
    def _create_base_image(self, width: int, height: int, style: str) -> Image.Image:
        """Create base image with background"""
        if style == "gradient":
            return self._create_gradient_background(width, height)
        elif style == "minimal":
            return Image.new('RGB', (width, height), self.brand_colors['light'])
        else:  # modern
            return self._create_modern_background(width, height)
    
    def _create_gradient_background(self, width: int, height: int) -> Image.Image:
        """Create gradient background"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create gradient from primary to secondary color
        for i in range(height):
            ratio = i / height
            r = int(self._hex_to_rgb(self.brand_colors['primary'])[0] * (1 - ratio) + 
                   self._hex_to_rgb(self.brand_colors['secondary'])[0] * ratio)
            g = int(self._hex_to_rgb(self.brand_colors['primary'])[1] * (1 - ratio) + 
                   self._hex_to_rgb(self.brand_colors['secondary'])[1] * ratio)
            b = int(self._hex_to_rgb(self.brand_colors['primary'])[2] * (1 - ratio) + 
                   self._hex_to_rgb(self.brand_colors['secondary'])[2] * ratio)
            
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        return img
    
    def _create_modern_background(self, width: int, height: int) -> Image.Image:
        """Create modern geometric background"""
        img = Image.new('RGB', (width, height), self.brand_colors['dark'])
        draw = ImageDraw.Draw(img)
        
        # Add geometric shapes
        # Triangle in corner
        draw.polygon(
            [(0, 0), (width // 3, 0), (0, height // 3)],
            fill=self.brand_colors['primary']
        )
        
        # Circle accent
        draw.ellipse(
            [width - 200, height - 200, width + 100, height + 100],
            fill=self.brand_colors['accent']
        )
        
        return img
    
    def _add_text_to_image(
        self,
        draw: ImageDraw.Draw,
        title: str,
        subtitle: Optional[str],
        width: int,
        height: int
    ):
        """Add text to image"""
        # Try to load custom font, fall back to default
        try:
            title_font = ImageFont.truetype("Arial.ttf", 60)
            subtitle_font = ImageFont.truetype("Arial.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Calculate text position
        margin = 80
        y_position = height // 3
        
        # Draw title (word wrap if needed)
        title_lines = self._wrap_text(title, title_font, width - 2 * margin)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            draw.text(
                (x_position, y_position),
                line,
                font=title_font,
                fill=self.brand_colors['light']
            )
            y_position += bbox[3] - bbox[1] + 20
        
        # Draw subtitle if provided
        if subtitle:
            y_position += 20
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            draw.text(
                (x_position, y_position),
                subtitle,
                font=subtitle_font,
                fill=self.brand_colors['light']
            )
    
    def _add_banner_text(
        self,
        draw: ImageDraw.Draw,
        title: str,
        category: Optional[str],
        width: int,
        height: int
    ):
        """Add text specifically for banner layout"""
        try:
            title_font = ImageFont.truetype("Arial.ttf", 80)
            category_font = ImageFont.truetype("Arial.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            category_font = ImageFont.load_default()
        
        # Left-aligned text for banner
        margin = 100
        y_position = height // 2 - 50
        
        # Draw category if provided
        if category:
            draw.text(
                (margin, y_position - 50),
                category.upper(),
                font=category_font,
                fill=self.brand_colors['accent']
            )
        
        # Draw title
        title_lines = self._wrap_text(title, title_font, width - 2 * margin)
        for line in title_lines[:2]:  # Max 2 lines for banner
            draw.text(
                (margin, y_position),
                line,
                font=title_font,
                fill=self.brand_colors['light']
            )
            bbox = draw.textbbox((0, 0), line, font=title_font)
            y_position += bbox[3] - bbox[1] + 20
    
    def _add_branding(self, img: Image.Image, draw: ImageDraw.Draw):
        """Add Re-Defined branding elements"""
        # Add logo text (in production, would load actual logo image)
        try:
            logo_font = ImageFont.truetype("Arial.ttf", 20)
        except:
            logo_font = ImageFont.load_default()
        
        logo_text = "RE-DEFINED"
        bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
        
        # Position in bottom right
        margin = 40
        x_position = img.width - (bbox[2] - bbox[0]) - margin
        y_position = img.height - (bbox[3] - bbox[1]) - margin
        
        draw.text(
            (x_position, y_position),
            logo_text,
            font=logo_font,
            fill=self.brand_colors['light']
        )
    
    def _add_design_elements(self, img: Image.Image, draw: ImageDraw.Draw, style: str):
        """Add decorative design elements"""
        if style == "modern":
            # Add accent lines
            draw.rectangle(
                [50, img.height - 100, 200, img.height - 95],
                fill=self.brand_colors['accent']
            )
            draw.rectangle(
                [50, img.height - 85, 150, img.height - 80],
                fill=self.brand_colors['primary']
            )
    
    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> list:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_filename(self, title: str) -> str:
        """Generate safe filename from title"""
        # Remove special characters and spaces
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.replace(' ', '_').lower()
        
        # Add timestamp for uniqueness
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{safe_title[:50]}_{timestamp}"
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _generate_dalle_image(self, prompt: str, image_type: str) -> Optional[str]:
        """Generate image using DALL-E API"""
        # Implementation would use OpenAI's DALL-E API
        # This is a placeholder
        logger.info(f"Would generate DALL-E image with prompt: {prompt}")
        return None
    
    def _generate_stability_image(self, prompt: str, image_type: str) -> Optional[str]:
        """Generate image using Stability AI"""
        # Implementation would use Stability AI API
        # This is a placeholder
        logger.info(f"Would generate Stability AI image with prompt: {prompt}")
        return None 