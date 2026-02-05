# Technical SEO Checklist: My Big Fat Shawarma

*Ensuring the website foundation supports search visibility*

---

## Overview

Technical SEO ensures search engines can crawl, index, and understand your website. This checklist covers all critical technical elements for a local restaurant website.

---

## Site Speed Optimization

### Core Web Vitals

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **LCP (Largest Contentful Paint)** | < 2.5 seconds | [Test] | [ ] |
| **FID (First Input Delay)** | < 100 ms | [Test] | [ ] |
| **CLS (Cumulative Layout Shift)** | < 0.1 | [Test] | [ ] |

### Speed Optimization Checklist

#### Images
- [ ] Compress all images (use TinyPNG, ShortPixel, or similar)
- [ ] Use WebP format where supported
- [ ] Implement lazy loading for below-fold images
- [ ] Specify image dimensions (width/height)
- [ ] Use responsive images with srcset

#### Code
- [ ] Minify CSS files
- [ ] Minify JavaScript files
- [ ] Remove unused CSS/JS
- [ ] Defer non-critical JavaScript
- [ ] Inline critical CSS

#### Server
- [ ] Enable GZIP compression
- [ ] Enable browser caching
- [ ] Use a CDN (Cloudflare recommended)
- [ ] Optimize hosting performance

### Testing Tools
- Google PageSpeed Insights: https://pagespeed.web.dev/
- GTmetrix: https://gtmetrix.com/
- WebPageTest: https://www.webpagetest.org/

---

## Mobile Optimization

### Mobile-First Requirements

| Element | Status | Notes |
|---------|--------|-------|
| **Responsive Design** | [ ] | Site adapts to all screen sizes |
| **Mobile Viewport** | [ ] | `<meta name="viewport" content="width=device-width, initial-scale=1">` |
| **Touch Targets** | [ ] | Buttons/links at least 48x48 pixels |
| **Font Size** | [ ] | Base font 16px minimum |
| **No Horizontal Scroll** | [ ] | Content fits viewport width |
| **Click-to-Call** | [ ] | Phone number is tappable |
| **Maps Integration** | [ ] | Address links to maps |

### Mobile Testing
- [ ] Test on actual mobile devices
- [ ] Google Mobile-Friendly Test: https://search.google.com/test/mobile-friendly

---

## Crawlability and Indexing

### Robots.txt

**Location:** mybigfatshawarma.com/robots.txt

**Recommended Content:**
```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /wp-admin/
Disallow: /wp-includes/

Sitemap: https://mybigfatshawarma.com/sitemap.xml
```

**Checklist:**
- [ ] Robots.txt exists
- [ ] Not blocking important pages
- [ ] Sitemap location specified
- [ ] Tested in Google Search Console

### XML Sitemap

**Location:** mybigfatshawarma.com/sitemap.xml

**Requirements:**
- [ ] Sitemap exists and is valid
- [ ] Includes all important pages
- [ ] Excludes noindex pages
- [ ] Updated automatically
- [ ] Submitted to Google Search Console
- [ ] Submitted to Bing Webmaster Tools

**Important Pages to Include:**
- Homepage
- Menu
- About
- Contact
- Location(s)
- Catering (if exists)
- Blog posts (if exists)

### Indexing Verification

| Page | Indexed? | Action Needed |
|------|----------|---------------|
| Homepage | [ ] | |
| Menu | [ ] | |
| About | [ ] | |
| Contact | [ ] | |

**How to Check:**
- Use `site:mybigfatshawarma.com` in Google
- Check Google Search Console Coverage report

---

## URL Structure

### Best Practices

| Practice | Status | Notes |
|----------|--------|-------|
| **HTTPS enabled** | [ ] | All pages on HTTPS |
| **No trailing slashes inconsistency** | [ ] | Pick one format |
| **Lowercase URLs** | [ ] | Avoid mixed case |
| **Descriptive URLs** | [ ] | `/menu/` not `/page?id=123` |
| **No special characters** | [ ] | Avoid &, %, etc. |
| **Short and clean** | [ ] | Fewer than 60 characters |

### Recommended URL Structure

```
https://mybigfatshawarma.com/ (homepage)
https://mybigfatshawarma.com/menu/
https://mybigfatshawarma.com/about/
https://mybigfatshawarma.com/contact/
https://mybigfatshawarma.com/catering/
https://mybigfatshawarma.com/order/
https://mybigfatshawarma.com/blog/
https://mybigfatshawarma.com/blog/what-is-shawarma/
```

---

## Redirects

### Redirect Checklist

- [ ] www redirects to non-www (or vice versa) consistently
- [ ] HTTP redirects to HTTPS
- [ ] No redirect chains (A→B→C should be A→C)
- [ ] No redirect loops
- [ ] Old URLs redirect to new pages (if site redesigned)
- [ ] 404 pages redirect to relevant content (where appropriate)

### Common Redirect Types

| Code | Use Case |
|------|----------|
| 301 | Permanent redirect (page moved forever) |
| 302 | Temporary redirect (page temporarily moved) |
| 308 | Permanent redirect (preserves HTTP method) |

---

## HTTPS and Security

### SSL Certificate

| Check | Status | Notes |
|-------|--------|-------|
| **SSL Certificate Active** | [ ] | |
| **Certificate Not Expired** | [ ] | Check expiration date |
| **Certificate Chain Valid** | [ ] | |
| **Force HTTPS** | [ ] | Redirect HTTP to HTTPS |
| **No Mixed Content** | [ ] | All resources on HTTPS |

### Security Headers

| Header | Recommended | Status |
|--------|-------------|--------|
| **Content-Security-Policy** | Configured | [ ] |
| **X-Frame-Options** | SAMEORIGIN | [ ] |
| **X-Content-Type-Options** | nosniff | [ ] |
| **Strict-Transport-Security** | Enabled | [ ] |

**Testing Tool:** https://securityheaders.com/

---

## Structured Data (Schema Markup)

### Required Schema Types

#### Restaurant Schema
- [ ] Implemented on homepage
- [ ] Includes all required properties
- [ ] Tested and validated

#### LocalBusiness Schema
- [ ] NAP information correct
- [ ] Opening hours accurate
- [ ] Geo coordinates included

#### Menu Schema (Optional but Recommended)
- [ ] Menu items structured
- [ ] Prices included
- [ ] Descriptions present

### Schema Implementation

**Method 1: JSON-LD (Recommended)**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "My Big Fat Shawarma",
  "image": "https://mybigfatshawarma.com/images/logo.jpg",
  "url": "https://mybigfatshawarma.com",
  "telephone": "(248) 977-4778",
  "priceRange": "$$",
  "servesCuisine": ["Mediterranean", "Middle Eastern", "Halal"],
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "4301 Orchard Lake Rd, Ste 110",
    "addressLocality": "West Bloomfield",
    "addressRegion": "MI",
    "postalCode": "48323",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "42.5389",
    "longitude": "-83.3816"
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
      "opens": "11:00",
      "closes": "21:00"
    }
  ],
  "menu": "https://mybigfatshawarma.com/menu",
  "acceptsReservations": false
}
</script>
```

### Testing
- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema Validator: https://validator.schema.org/

---

## On-Page Technical Elements

### Title Tags

| Requirement | Status |
|-------------|--------|
| Unique for each page | [ ] |
| 50-60 characters | [ ] |
| Primary keyword included | [ ] |
| Brand name at end | [ ] |

### Meta Descriptions

| Requirement | Status |
|-------------|--------|
| Unique for each page | [ ] |
| 150-160 characters | [ ] |
| Includes call-to-action | [ ] |
| Compelling and relevant | [ ] |

### Header Tags

| Requirement | Status |
|-------------|--------|
| One H1 per page | [ ] |
| H1 includes primary keyword | [ ] |
| Logical hierarchy (H1>H2>H3) | [ ] |
| Headers describe content | [ ] |

### Image Optimization

| Requirement | Status |
|-------------|--------|
| Descriptive file names | [ ] |
| Alt text on all images | [ ] |
| Compressed for web | [ ] |
| Responsive images | [ ] |

---

## Canonical Tags

### Implementation

- [ ] Every page has a canonical tag
- [ ] Canonical points to preferred URL
- [ ] No conflicting canonicals
- [ ] Self-referencing canonicals on main pages

**Example:**
```html
<link rel="canonical" href="https://mybigfatshawarma.com/menu/" />
```

---

## International and Language

### For Single-Location English Site

- [ ] `<html lang="en">` attribute set
- [ ] Content in English
- [ ] No hreflang needed (single language)

---

## Error Pages

### 404 Page

- [ ] Custom 404 page exists
- [ ] Helpful content and navigation
- [ ] Search functionality
- [ ] Link to homepage
- [ ] Consistent branding

### Server Error Handling

- [ ] 5xx errors return appropriate status codes
- [ ] Custom error pages where needed
- [ ] Error monitoring in place

---

## Performance Monitoring

### Tools to Set Up

| Tool | Purpose | Status |
|------|---------|--------|
| **Google Search Console** | Search performance | [ ] |
| **Google Analytics 4** | Traffic analytics | [ ] |
| **Bing Webmaster Tools** | Bing search data | [ ] |
| **Uptime monitoring** | Site availability | [ ] |

### Regular Checks

| Task | Frequency |
|------|-----------|
| Check Search Console for errors | Weekly |
| Review Core Web Vitals | Monthly |
| Run full site crawl | Monthly |
| Check indexing status | Weekly |
| Review 404 errors | Weekly |

---

## Technical SEO Audit Schedule

### Weekly Tasks
- [ ] Check Google Search Console for issues
- [ ] Review any new 404 errors
- [ ] Verify site is loading properly

### Monthly Tasks
- [ ] Run PageSpeed test
- [ ] Check Core Web Vitals
- [ ] Review indexing status
- [ ] Test mobile-friendliness
- [ ] Validate structured data

### Quarterly Tasks
- [ ] Full technical audit
- [ ] Competitive technical comparison
- [ ] Review and update schema
- [ ] Clean up redirect chains
- [ ] Review security headers

---

## Implementation Priority

### Critical (Week 1)
- [ ] Verify HTTPS is active
- [ ] Check mobile-friendliness
- [ ] Verify Google indexing
- [ ] Set up Google Search Console

### High (Month 1)
- [ ] Implement schema markup
- [ ] Optimize page speed to 90+
- [ ] Fix any crawl errors
- [ ] Submit sitemap

### Medium (Quarter 1)
- [ ] Implement all security headers
- [ ] Optimize images comprehensively
- [ ] Set up monitoring tools
- [ ] Create custom 404 page

---

*Last Updated: 2026-02-05*
*Next Technical Review: Monthly*
