# iSwitch Roofs Implementation Roadmap

## Quick Start Checklist

### Week 1: Critical Fixes ⚡
- [ ] **Day 1:** Fix robots meta tag conflicts
- [ ] **Day 2:** Add testimonials plugin and initial content
- [ ] **Day 3:** Implement security headers via .htaccess
- [ ] **Day 4:** Set up Google Review display widget
- [ ] **Day 5:** Create before/after gallery structure

### Week 2: Performance & Trust 🚀
- [ ] **Day 6-7:** Implement Cloudflare CDN
- [ ] **Day 8-9:** Add live chat (Tidio or Intercom)
- [ ] **Day 10:** Launch Google Ads campaign
- [ ] **Day 11:** Create first 3 city landing pages
- [ ] **Day 12:** Set up automated review requests

## Detailed Implementation Guide

### 1. SEO Technical Fixes

#### Fix Robots Directives
**File:** header.php or SEO plugin settings
```php
// Remove conflicting noindex
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
```

#### Add Canonical URLs
```php
<link rel="canonical" href="<?php echo get_permalink(); ?>" />
```

#### Create XML Sitemap
- Install Yoast SEO or RankMath
- Configure sitemap settings
- Submit to Google Search Console

### 2. Social Proof Implementation

#### Testimonials Section
**Plugin Options:**
- Strong Testimonials (WordPress)
- Testimonial Rotator
- Custom ACF implementation

**Schema Markup:**
```json
{
  "@type": "Review",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "5",
    "bestRating": "5"
  },
  "author": {
    "@type": "Person",
    "name": "Customer Name"
  }
}
```

#### Google Reviews Integration
**Tools:**
- Google Places API
- Reviews.io widget
- Birdeye platform

**Implementation:**
```html
<div id="google-reviews-widget">
  <!-- Widget code here -->
</div>
```

### 3. Security Headers Configuration

#### .htaccess Updates
```apache
# Security Headers
Header set X-Frame-Options "SAMEORIGIN"
Header set X-Content-Type-Options "nosniff"
Header set Strict-Transport-Security "max-age=31536000; includeSubDomains"
Header set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' *.google.com *.facebook.com; style-src 'self' 'unsafe-inline'"
```

### 4. Performance Optimization

#### Cloudflare Setup
1. Create free Cloudflare account
2. Add site and update nameservers
3. Configure settings:
   - Auto Minify: ON
   - Brotli: ON
   - Browser Cache TTL: 4 hours
   - Always Online: ON

#### Image Optimization
```bash
# Install WebP conversion
npm install --save-dev imagemin imagemin-webp

# Convert images
for file in *.{jpg,png}; do
  cwebp -q 80 "$file" -o "${file%.*}.webp"
done
```

### 5. Lead Generation Enhancements

#### Live Chat Setup
**Intercom Installation:**
```javascript
window.intercomSettings = {
  app_id: "YOUR_APP_ID",
  custom_launcher_selector: '.chat-trigger'
};
```

#### Exit Intent Popup
```javascript
document.addEventListener('mouseleave', function(e) {
  if (e.clientY < 0) {
    // Show exit intent popup
    document.getElementById('exit-popup').style.display = 'block';
  }
});
```

### 6. Local SEO Pages

#### City Page Template
```php
<?php
/* Template Name: City Landing Page */

$city = get_field('city_name');
$population = get_field('population');
$weather_stats = get_field('weather_stats');
?>

<h1>Roof Replacement <?php echo $city; ?>, Michigan</h1>
<p>Serving <?php echo number_format($population); ?> residents with honest roofing services...</p>
```

#### Schema for Local Pages
```json
{
  "@type": "LocalBusiness",
  "name": "iSwitch Roofs - <?php echo $city; ?>",
  "areaServed": {
    "@type": "City",
    "name": "<?php echo $city; ?>"
  }
}
```

### 7. Google Ads Campaign Structure

#### Campaign Setup
```
Campaign: Roof Replacement - Southeast Michigan
├── Ad Group: Emergency Repair
│   ├── Keywords: "emergency roof repair [city]"
│   └── Ads: Urgency-focused copy
├── Ad Group: Storm Damage
│   ├── Keywords: "storm damage roof michigan"
│   └── Ads: Insurance claim assistance
└── Ad Group: Replacement
    ├── Keywords: "roof replacement [city]"
    └── Ads: Value proposition focus
```

#### Landing Page Optimization
- Match ad copy to landing page headlines
- Include form above fold
- Add trust badges near CTA
- Mobile-specific bid adjustments

### 8. Email Marketing Setup

#### Welcome Series Flow
```
Day 0: Welcome + Free Roof Maintenance Guide
Day 3: Common Roofing Problems to Watch
Day 7: Seasonal Preparation Tips
Day 14: Customer Success Story
Day 21: Special Offer
```

#### Automation Triggers
- Form submission → Welcome series
- Quote request → Follow-up sequence
- Service complete → Review request
- 6 months post-service → Maintenance reminder

### 9. Content Calendar

#### Weekly Blog Topics
**Month 1:**
- Week 1: "Michigan Weather vs Your Roof"
- Week 2: "Insurance Claims Made Simple"
- Week 3: "Solar + New Roof Benefits"
- Week 4: "Seasonal Maintenance Guide"

**Month 2:**
- Week 1: "Warning Signs You Need a New Roof"
- Week 2: "Choosing the Right Shingles"
- Week 3: "Storm Damage Assessment"
- Week 4: "Financing Your Roof"

### 10. Tracking & Analytics

#### UTM Parameter Structure
```
utm_source=google
utm_medium=cpc
utm_campaign=roof-replacement
utm_content=ad-version-a
utm_term=[keyword]
```

#### Conversion Tracking
```javascript
// Form submission tracking
gtag('event', 'conversion', {
  'send_to': 'AW-XXXXXXXXX/XXXXXXXXX',
  'value': 15000.0,
  'currency': 'USD'
});
```

## Resource Requirements

### Tools & Subscriptions
| Tool | Purpose | Cost/Month |
|------|---------|------------|
| Cloudflare | CDN & Security | $20 |
| Intercom | Live Chat | $100 |
| Mailchimp | Email Marketing | $75 |
| SEMrush | SEO Tracking | $120 |
| CallRail | Call Tracking | $45 |
| Canva Pro | Design | $13 |
| **Total** | | **$373** |

### Team Requirements
- **Week 1-2:** 40 hours developer time
- **Ongoing:** 10 hours/week marketing management
- **Content:** 5 hours/week writing
- **Design:** 3 hours/week graphics

## Success Milestones

### 30-Day Targets
- [ ] 100+ Google Reviews displayed
- [ ] 3 city pages ranking top 10
- [ ] 25% increase in form submissions
- [ ] Live chat generating 20+ leads/week

### 60-Day Targets
- [ ] 4.5+ star average rating
- [ ] 10 city pages created
- [ ] Email list: 500+ subscribers
- [ ] Google Ads CTR: 5%+

### 90-Day Targets
- [ ] Position 1-3 for main keywords
- [ ] 100+ leads/month
- [ ] $40 cost per lead
- [ ] 5% website conversion rate

## Contingency Plans

### If Reviews Don't Improve
- Implement incentive program
- Personal outreach to happy customers
- Video testimonial campaign

### If Traffic Doesn't Increase
- Expand Google Ads budget
- Guest posting campaign
- Local partnership development

### If Conversions Stay Low
- A/B test landing pages
- Offer stronger guarantees
- Implement chat proactively

## Next Steps

1. **Today:** Share this roadmap with team
2. **Tomorrow:** Begin Week 1 critical fixes
3. **This Week:** Set up tracking systems
4. **Next Week:** Launch first campaigns
5. **This Month:** Complete Phase 1 & 2

---

*Last Updated: September 26, 2025*
*Next Review: October 26, 2025*