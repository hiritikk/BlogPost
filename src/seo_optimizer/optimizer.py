"""
SEO optimizer for blog posts
"""
import yake
from typing import List, Dict, Optional
from loguru import logger
from src.utils.text_utils import extract_keywords, truncate_text
from config.settings import settings

class SEOOptimizer:
    """Optimizes blog posts for search engines"""
    
    def __init__(self):
        self.target_keywords = settings.target_keywords
        self.meta_description_length = settings.default_meta_description_length
    
    def optimize_blog_post(self, blog_post: Dict) -> Dict:
        """
        Optimize a blog post for SEO
        
        Args:
            blog_post: Dictionary containing blog content
            
        Returns:
            Dictionary with SEO optimizations
        """
        optimizations = {}
        
        # Generate or optimize meta description
        optimizations['meta_description'] = self._optimize_meta_description(
            blog_post.get('meta_description', ''),
            blog_post.get('content', ''),
            blog_post.get('title', '')
        )
        
        # Extract and optimize keywords
        optimizations['keywords'] = self._optimize_keywords(
            blog_post.get('content', ''),
            blog_post.get('keywords', [])
        )
        
        # Generate SEO title if needed
        optimizations['seo_title'] = self._optimize_title(
            blog_post.get('title', ''),
            optimizations['keywords']
        )
        
        # Check content for SEO issues
        optimizations['seo_score'] = self._calculate_seo_score(
            blog_post.get('content', ''),
            optimizations
        )
        
        # Generate schema markup
        optimizations['schema_markup'] = self._generate_schema_markup(blog_post)
        
        # URL slug optimization
        optimizations['url_suggestions'] = self._optimize_url_slug(
            blog_post.get('slug', ''),
            optimizations['keywords']
        )
        
        return optimizations
    
    def _optimize_meta_description(
        self,
        current_description: str,
        content: str,
        title: str
    ) -> str:
        """Optimize or generate meta description"""
        
        # If description exists and is good length, check if it needs improvement
        if current_description and 120 <= len(current_description) <= 160:
            # Check if it contains target keywords
            has_keywords = any(
                keyword.lower() in current_description.lower()
                for keyword in self.target_keywords
            )
            
            if has_keywords:
                return current_description
        
        # Generate new meta description
        # Extract first meaningful sentences
        sentences = content.split('.')[:3]
        description = '. '.join(sentences).strip()
        
        # Include title keywords if possible
        if len(description) < 100:
            description = f"{title}. {description}"
        
        # Truncate to proper length
        description = truncate_text(description, self.meta_description_length, '...')
        
        # Ensure at least one target keyword is included
        for keyword in self.target_keywords:
            if keyword.lower() not in description.lower() and len(description) < 140:
                description = f"{description} Learn more about {keyword}."
                break
        
        return truncate_text(description, self.meta_description_length, '...')
    
    def _optimize_keywords(self, content: str, existing_keywords: List[str]) -> List[str]:
        """Extract and optimize keywords"""
        
        # Use YAKE for keyword extraction
        kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # max n-grams
            dedupLim=0.7,
            top=20,
            features=None
        )
        
        extracted = kw_extractor.extract_keywords(content)
        yake_keywords = [kw[0] for kw in extracted]
        
        # Combine with existing keywords
        all_keywords = list(set(existing_keywords + yake_keywords))
        
        # Prioritize target keywords
        prioritized = []
        
        # Add target keywords that appear in content
        for target in self.target_keywords:
            if any(target.lower() in kw.lower() for kw in all_keywords):
                prioritized.append(target)
        
        # Add other high-value keywords
        for kw in all_keywords:
            if kw not in prioritized and len(prioritized) < 10:
                prioritized.append(kw)
        
        return prioritized[:10]  # Limit to 10 keywords
    
    def _optimize_title(self, title: str, keywords: List[str]) -> str:
        """Optimize title for SEO"""
        
        # Check if title length is good (50-60 characters ideal)
        if 50 <= len(title) <= 60:
            return title
        
        # If too long, truncate
        if len(title) > 60:
            return truncate_text(title, 60, '')
        
        # If too short, consider adding a keyword
        if len(title) < 50 and keywords:
            # Find a keyword not already in title
            for keyword in keywords[:3]:
                if keyword.lower() not in title.lower():
                    new_title = f"{title} - {keyword}"
                    if len(new_title) <= 60:
                        return new_title
        
        return title
    
    def _calculate_seo_score(self, content: str, optimizations: Dict) -> Dict:
        """Calculate SEO score and provide recommendations"""
        
        score = 0
        max_score = 100
        recommendations = []
        
        # Check meta description
        meta_desc = optimizations.get('meta_description', '')
        if meta_desc:
            if 120 <= len(meta_desc) <= 160:
                score += 10
            else:
                recommendations.append("Optimize meta description length (120-160 chars)")
        else:
            recommendations.append("Add meta description")
        
        # Check keywords presence in content
        keywords = optimizations.get('keywords', [])
        if keywords:
            keyword_density = sum(
                content.lower().count(kw.lower()) for kw in keywords
            ) / len(content.split()) * 100
            
            if 1 <= keyword_density <= 3:
                score += 15
            elif keyword_density < 1:
                recommendations.append("Increase keyword density")
            else:
                recommendations.append("Reduce keyword density (too high)")
        
        # Check content length
        word_count = len(content.split())
        if word_count >= 300:
            score += 15
            if word_count >= 500:
                score += 10
        else:
            recommendations.append("Increase content length (min 300 words)")
        
        # Check headings (looking for markdown headers)
        if '##' in content:
            score += 10
            if '###' in content:
                score += 5
        else:
            recommendations.append("Add subheadings to structure content")
        
        # Check for links (internal/external)
        if 'http' in content or '[' in content:
            score += 10
        else:
            recommendations.append("Add relevant internal/external links")
        
        # Check title optimization
        title = optimizations.get('seo_title', '')
        if title and any(kw.lower() in title.lower() for kw in self.target_keywords):
            score += 10
        else:
            recommendations.append("Include target keywords in title")
        
        # Check for images (looking for markdown image syntax)
        if '![' in content:
            score += 10
        else:
            recommendations.append("Add images with alt text")
        
        # Calculate final score percentage
        score_percentage = min(100, (score / max_score) * 100)
        
        return {
            'score': score_percentage,
            'recommendations': recommendations,
            'details': {
                'word_count': word_count,
                'keyword_density': keyword_density if keywords else 0,
                'meta_description_length': len(meta_desc),
                'has_headings': '##' in content,
                'has_links': 'http' in content or '[' in content,
                'has_images': '![' in content
            }
        }
    
    def _generate_schema_markup(self, blog_post: Dict) -> Dict:
        """Generate schema.org markup for the blog post"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": blog_post.get('title', ''),
            "description": blog_post.get('meta_description', ''),
            "keywords": ", ".join(blog_post.get('keywords', [])),
            "wordCount": blog_post.get('word_count', 0),
            "author": {
                "@type": "Organization",
                "name": "Re-Defined"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Re-Defined",
                "url": "https://re-defined.ca"
            },
            "datePublished": blog_post.get('published_date', ''),
            "dateModified": blog_post.get('updated_at', ''),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://re-defined.ca/blog/{blog_post.get('slug', '')}"
            }
        }
        
        # Add image if available
        if blog_post.get('thumbnail_url'):
            schema['image'] = {
                "@type": "ImageObject",
                "url": blog_post.get('thumbnail_url'),
                "width": 1200,
                "height": 630
            }
        
        return schema
    
    def _optimize_url_slug(self, current_slug: str, keywords: List[str]) -> Dict:
        """Provide URL slug optimization suggestions"""
        
        suggestions = {
            'current': current_slug,
            'optimized': current_slug,
            'recommendations': []
        }
        
        # Check slug length (ideal: 3-5 words)
        slug_words = current_slug.split('-')
        if len(slug_words) > 5:
            suggestions['recommendations'].append("Consider shortening URL slug")
            # Suggest shorter version
            suggestions['optimized'] = '-'.join(slug_words[:5])
        
        # Check for stop words
        stop_words = ['a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for']
        has_stop_words = any(word in stop_words for word in slug_words)
        if has_stop_words:
            suggestions['recommendations'].append("Remove stop words from URL")
            # Remove stop words
            optimized_words = [w for w in slug_words if w not in stop_words]
            suggestions['optimized'] = '-'.join(optimized_words)
        
        # Check for keyword presence
        slug_lower = current_slug.lower()
        has_keyword = any(
            kw.lower().replace(' ', '-') in slug_lower 
            for kw in keywords[:3]
        )
        
        if not has_keyword and keywords:
            suggestions['recommendations'].append("Include primary keyword in URL")
        
        return suggestions
    
    def generate_seo_report(self, blog_post: Dict) -> str:
        """Generate a comprehensive SEO report"""
        
        optimizations = self.optimize_blog_post(blog_post)
        seo_score = optimizations['seo_score']
        
        report = f"""
# SEO Report for: {blog_post.get('title', 'Untitled')}

## Overall Score: {seo_score['score']:.1f}/100

### Summary
- Word Count: {seo_score['details']['word_count']}
- Keyword Density: {seo_score['details']['keyword_density']:.2f}%
- Meta Description Length: {seo_score['details']['meta_description_length']}

### Optimizations Applied:
1. **Meta Description**: {optimizations['meta_description'][:50]}...
2. **Keywords**: {', '.join(optimizations['keywords'][:5])}
3. **SEO Title**: {optimizations['seo_title']}

### Recommendations:
"""
        
        for i, rec in enumerate(seo_score['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        return report 