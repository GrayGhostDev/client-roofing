#!/usr/bin/env python3
"""
Comprehensive UI/UX Testing for iSwitch Roofs CRM Dashboard
Tests frontend functionality, responsiveness, and user experience elements
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class RoofingCRMTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8001"
        self.screenshots_dir = Path("screenshots")
        self.results = {
            "test_run_id": datetime.now().isoformat(),
            "base_url": self.base_url,
            "backend_url": self.backend_url,
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }

        # Ensure screenshots directory exists
        self.screenshots_dir.mkdir(exist_ok=True)

    async def log_test(self, test_name, status, details=None, screenshot_path=None):
        """Log test results"""
        test_result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "screenshot": screenshot_path
        }

        self.results["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1

        if status == "PASSED":
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}")
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
            self.results["summary"]["errors"].append(f"{test_name}: {details}")
            print(f"❌ {test_name}: {details}")
        else:
            print(f"⚠️  {test_name}: {details}")

    async def take_screenshot(self, page, name):
        """Take and save screenshot"""
        screenshot_path = self.screenshots_dir / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)

    async def test_frontend_accessibility(self, page):
        """Test basic frontend accessibility and loading"""
        try:
            # Navigate to main page
            response = await page.goto(self.base_url, wait_until="networkidle")

            if response.status == 500:
                await self.log_test(
                    "Frontend HTTP Status",
                    "FAILED",
                    {"status_code": response.status, "message": "Server returning HTTP 500"}
                )

                # Try to get error details from the page
                error_text = await page.locator("body").text_content()
                screenshot_path = await self.take_screenshot(page, "http_500_error")

                await self.log_test(
                    "Error Page Analysis",
                    "FAILED",
                    {"error_content": error_text[:500], "full_error": error_text},
                    screenshot_path
                )
                return False
            else:
                await self.log_test("Frontend HTTP Status", "PASSED", {"status_code": response.status})
                return True

        except Exception as e:
            await self.log_test("Frontend Accessibility", "FAILED", {"error": str(e)})
            return False

    async def test_page_title_and_metadata(self, page):
        """Test page title and basic metadata"""
        try:
            title = await page.title()
            await self.log_test("Page Title", "PASSED" if title else "FAILED", {"title": title})

            # Check for viewport meta tag
            viewport = await page.locator('meta[name="viewport"]').count()
            await self.log_test("Viewport Meta Tag", "PASSED" if viewport > 0 else "FAILED", {"found": viewport > 0})

        except Exception as e:
            await self.log_test("Page Metadata", "FAILED", {"error": str(e)})

    async def test_main_dashboard_elements(self, page):
        """Test main dashboard components and layout"""
        try:
            # Check for main heading
            heading = await page.locator("h1, h2, h3").first.text_content() if await page.locator("h1, h2, h3").count() > 0 else None
            await self.log_test("Main Heading", "PASSED" if heading else "FAILED", {"heading": heading})

            # Check for navigation elements
            nav_count = await page.locator("nav, [role='navigation']").count()
            await self.log_test("Navigation Elements", "PASSED" if nav_count > 0 else "FAILED", {"nav_elements": nav_count})

            # Check for main content area
            main_content = await page.locator("main, [role='main'], .main-content").count()
            await self.log_test("Main Content Area", "PASSED" if main_content > 0 else "FAILED", {"main_elements": main_content})

            # Take full page screenshot
            screenshot_path = await self.take_screenshot(page, "main_dashboard")
            await self.log_test("Dashboard Screenshot", "PASSED", {"screenshot_taken": True}, screenshot_path)

        except Exception as e:
            await self.log_test("Dashboard Elements", "FAILED", {"error": str(e)})

    async def test_responsive_design(self, page):
        """Test responsive design across different viewport sizes"""
        viewports = [
            {"name": "Mobile", "width": 375, "height": 667},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Desktop", "width": 1920, "height": 1080}
        ]

        for viewport in viewports:
            try:
                await page.set_viewport_size(viewport["width"], viewport["height"])
                await page.wait_for_timeout(1000)  # Wait for responsive changes

                screenshot_path = await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")

                # Check if content is visible and not overlapping
                body = await page.locator("body").bounding_box()
                if body:
                    await self.log_test(
                        f"Responsive - {viewport['name']}",
                        "PASSED",
                        {"viewport": viewport, "content_visible": True},
                        screenshot_path
                    )
                else:
                    await self.log_test(
                        f"Responsive - {viewport['name']}",
                        "FAILED",
                        {"viewport": viewport, "content_visible": False},
                        screenshot_path
                    )

            except Exception as e:
                await self.log_test(f"Responsive - {viewport['name']}", "FAILED", {"error": str(e)})

    async def test_interactive_elements(self, page):
        """Test interactive elements like buttons, links, forms"""
        try:
            # Check for buttons
            buttons = await page.locator("button, [role='button']").count()
            await self.log_test("Interactive Buttons", "PASSED" if buttons > 0 else "INFO", {"button_count": buttons})

            # Check for links
            links = await page.locator("a[href]").count()
            await self.log_test("Navigation Links", "PASSED" if links > 0 else "INFO", {"link_count": links})

            # Check for form elements
            forms = await page.locator("form, input, select, textarea").count()
            await self.log_test("Form Elements", "PASSED" if forms > 0 else "INFO", {"form_elements": forms})

            # Test clicking first button if available
            if buttons > 0:
                first_button = page.locator("button, [role='button']").first
                button_text = await first_button.text_content()

                try:
                    await first_button.click(timeout=5000)
                    await self.log_test("Button Interaction", "PASSED", {"clicked_button": button_text})
                except Exception as e:
                    await self.log_test("Button Interaction", "FAILED", {"error": str(e), "button_text": button_text})

        except Exception as e:
            await self.log_test("Interactive Elements", "FAILED", {"error": str(e)})

    async def test_navigation_components(self, page):
        """Test navigation between different dashboard sections"""
        navigation_tests = [
            {"selector": "a[href*='leads'], a[href*='lead']", "name": "Leads Navigation"},
            {"selector": "a[href*='project'], a[href*='projects']", "name": "Projects Navigation"},
            {"selector": "a[href*='customer'], a[href*='customers']", "name": "Customers Navigation"},
            {"selector": "a[href*='analytic'], a[href*='analytics']", "name": "Analytics Navigation"},
            {"selector": "a[href*='appointment'], a[href*='appointments']", "name": "Appointments Navigation"},
            {"selector": "a[href*='setting'], a[href*='settings']", "name": "Settings Navigation"},
        ]

        for nav_test in navigation_tests:
            try:
                nav_element = page.locator(nav_test["selector"]).first
                if await nav_element.count() > 0:
                    href = await nav_element.get_attribute("href")
                    text = await nav_element.text_content()
                    await self.log_test(nav_test["name"], "PASSED", {"href": href, "text": text})

                    # Try to click and navigate
                    try:
                        await nav_element.click(timeout=3000)
                        await page.wait_for_timeout(2000)
                        current_url = page.url
                        screenshot_path = await self.take_screenshot(page, f"nav_{nav_test['name'].lower().replace(' ', '_')}")
                        await self.log_test(f"{nav_test['name']} - Click Test", "PASSED", {"new_url": current_url}, screenshot_path)

                        # Navigate back to main page for next test
                        await page.goto(self.base_url, wait_until="networkidle")

                    except Exception as click_error:
                        await self.log_test(f"{nav_test['name']} - Click Test", "FAILED", {"error": str(click_error)})
                else:
                    await self.log_test(nav_test["name"], "FAILED", {"reason": "Navigation element not found"})

            except Exception as e:
                await self.log_test(nav_test["name"], "FAILED", {"error": str(e)})

    async def test_performance_metrics(self, page):
        """Test basic performance metrics"""
        try:
            # Measure page load time
            start_time = datetime.now()
            await page.reload(wait_until="networkidle")
            end_time = datetime.now()
            load_time = (end_time - start_time).total_seconds()

            await self.log_test("Page Load Time", "PASSED" if load_time < 5 else "FAILED", {"load_time_seconds": load_time})

            # Check for JavaScript errors in console
            errors = []

            def handle_console(msg):
                if msg.type == "error":
                    errors.append(msg.text)

            page.on("console", handle_console)
            await page.reload(wait_until="networkidle")

            await self.log_test("JavaScript Errors", "PASSED" if len(errors) == 0 else "FAILED", {"errors": errors})

        except Exception as e:
            await self.log_test("Performance Metrics", "FAILED", {"error": str(e)})

    async def test_backend_connectivity(self, page):
        """Test if frontend can communicate with backend API"""
        try:
            # Inject JavaScript to test API connectivity
            api_test_result = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('http://localhost:8001/api/health');
                        return {
                            status: response.status,
                            ok: response.ok,
                            statusText: response.statusText
                        };
                    } catch (error) {
                        return {
                            error: error.message
                        };
                    }
                }
            """)

            if "error" in api_test_result:
                await self.log_test("Backend API Connectivity", "FAILED", api_test_result)
            else:
                await self.log_test("Backend API Connectivity", "PASSED" if api_test_result.get("ok") else "FAILED", api_test_result)

        except Exception as e:
            await self.log_test("Backend Connectivity", "FAILED", {"error": str(e)})

    async def test_accessibility_features(self, page):
        """Test basic accessibility features"""
        try:
            # Check for alt text on images
            images = await page.locator("img").count()
            images_with_alt = await page.locator("img[alt]").count()

            await self.log_test("Image Alt Text", "PASSED" if images == 0 or images_with_alt == images else "FAILED",
                              {"total_images": images, "images_with_alt": images_with_alt})

            # Check for heading hierarchy
            headings = await page.locator("h1, h2, h3, h4, h5, h6").count()
            await self.log_test("Heading Elements", "PASSED" if headings > 0 else "INFO", {"heading_count": headings})

            # Check for ARIA labels
            aria_labels = await page.locator("[aria-label], [aria-labelledby]").count()
            await self.log_test("ARIA Labels", "PASSED" if aria_labels > 0 else "INFO", {"aria_elements": aria_labels})

        except Exception as e:
            await self.log_test("Accessibility Features", "FAILED", {"error": str(e)})

    async def run_comprehensive_test(self):
        """Run all UI/UX tests"""
        print("🚀 Starting Comprehensive UI/UX Testing for iSwitch Roofs CRM Dashboard")
        print(f"📍 Frontend URL: {self.base_url}")
        print(f"📍 Backend URL: {self.backend_url}")
        print("=" * 80)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                # Run all test suites
                await self.test_frontend_accessibility(page)

                # Only run other tests if frontend is accessible
                if self.results["summary"]["failed"] == 0:
                    await self.test_page_title_and_metadata(page)
                    await self.test_main_dashboard_elements(page)
                    await self.test_responsive_design(page)
                    await self.test_interactive_elements(page)
                    await self.test_navigation_components(page)
                    await self.test_performance_metrics(page)
                    await self.test_backend_connectivity(page)
                    await self.test_accessibility_features(page)
                else:
                    print("⚠️  Skipping additional tests due to frontend accessibility issues")

            except Exception as e:
                await self.log_test("Test Suite Execution", "FAILED", {"error": str(e)})

            finally:
                await browser.close()

        # Generate final report
        await self.generate_report()

    async def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 UI/UX TEST SUMMARY")
        print("=" * 80)

        summary = self.results["summary"]
        print(f"📈 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📸 Screenshots: {len(list(self.screenshots_dir.glob('*.png')))}")

        if summary["errors"]:
            print("\n🐛 CRITICAL ISSUES FOUND:")
            for error in summary["errors"]:
                print(f"   • {error}")

        # Save detailed JSON report
        report_path = Path("ui_ux_test_report.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")
        print(f"📁 Screenshots saved to: {self.screenshots_dir}")

        # Generate recommendations
        await self.generate_recommendations()

    async def generate_recommendations(self):
        """Generate UX improvement recommendations"""
        print("\n🎯 UX IMPROVEMENT RECOMMENDATIONS:")
        print("=" * 50)

        failed_tests = [test for test in self.results["tests"] if test["status"] == "FAILED"]

        if any("HTTP 500" in test["test_name"] for test in failed_tests):
            print("🚨 CRITICAL: Fix HTTP 500 errors on frontend")
            print("   - Check React Router configuration")
            print("   - Verify all component imports")
            print("   - Check for JavaScript compilation errors")

        if any("Responsive" in test["test_name"] for test in failed_tests):
            print("📱 RESPONSIVE: Improve mobile/tablet layouts")
            print("   - Test breakpoints and media queries")
            print("   - Ensure content scales properly")

        if any("Navigation" in test["test_name"] for test in failed_tests):
            print("🧭 NAVIGATION: Improve navigation structure")
            print("   - Ensure all main sections are accessible")
            print("   - Add proper routing for SPA navigation")

        if any("Performance" in test["test_name"] for test in failed_tests):
            print("⚡ PERFORMANCE: Optimize loading times")
            print("   - Implement code splitting")
            print("   - Optimize image loading")
            print("   - Add loading indicators")

        if any("Backend" in test["test_name"] for test in failed_tests):
            print("🔌 API: Improve backend connectivity")
            print("   - Verify API endpoints are accessible")
            print("   - Add proper error handling")
            print("   - Implement retry mechanisms")

async def main():
    """Main entry point"""
    tester = RoofingCRMTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())