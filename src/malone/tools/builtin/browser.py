from __future__ import annotations

import asyncio
import json

from malone.tools.base import BaseTool

# Lazy-loaded to avoid import cost when not used
_browser = None
_page = None


async def _get_page():
    """Get or create the browser page (lazy singleton)."""
    global _browser, _page
    if _page is None:
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
        _page = await _browser.new_page()
    return _page


class BrowseWebTool(BaseTool):
    """Navigate to a URL and return the page content."""

    @property
    def name(self) -> str:
        return "browse_web"

    @property
    def description(self) -> str:
        return (
            "Navigate to a URL and return the visible text content of the page. "
            "Use this to read web pages, check device web UIs, or gather information. "
            "The browser session persists across calls so you can navigate multi-page flows."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to",
                },
            },
            "required": ["url"],
        }

    async def execute(self, url: str) -> str:
        try:
            page = await _get_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            title = await page.title()
            # Get visible text, truncated to avoid flooding
            text = await page.inner_text("body")
            text = text.strip()[:3000]
            return f"Page: {title}\nURL: {page.url}\n\n{text}"
        except Exception as e:
            return f"Error browsing {url}: {e}"


class BrowserClickTool(BaseTool):
    """Click an element on the current page."""

    @property
    def name(self) -> str:
        return "browser_click"

    @property
    def description(self) -> str:
        return (
            "Click an element on the current browser page by CSS selector or text. "
            "Use after browse_web to interact with the page. "
            "Examples: selector='button#submit', text='Sign In', selector='a[href=\"/book\"]'."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector of the element to click",
                },
                "text": {
                    "type": "string",
                    "description": "Visible text of the element to click (alternative to selector)",
                },
            },
            "required": [],
        }

    async def execute(self, selector: str = "", text: str = "") -> str:
        try:
            page = await _get_page()
            if text:
                await page.get_by_text(text, exact=False).first.click(timeout=5000)
            elif selector:
                await page.click(selector, timeout=5000)
            else:
                return "Error: Provide either 'selector' or 'text'."

            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            title = await page.title()
            return f"Clicked. Now on: {title} ({page.url})"
        except Exception as e:
            return f"Error clicking: {e}"


class BrowserFillTool(BaseTool):
    """Fill in a form field on the current page."""

    @property
    def name(self) -> str:
        return "browser_fill"

    @property
    def description(self) -> str:
        return (
            "Fill in a form field on the current browser page. "
            "Identify the field by CSS selector, label text, or placeholder text."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector of the input field (e.g. 'input[name=\"email\"]')",
                },
                "label": {
                    "type": "string",
                    "description": "Label text associated with the field (alternative to selector)",
                },
                "value": {
                    "type": "string",
                    "description": "The value to type into the field",
                },
            },
            "required": ["value"],
        }

    async def execute(self, value: str, selector: str = "", label: str = "") -> str:
        try:
            page = await _get_page()
            if label:
                await page.get_by_label(label).fill(value)
            elif selector:
                await page.fill(selector, value)
            else:
                return "Error: Provide either 'selector' or 'label'."
            return f"Filled '{value}' into field."
        except Exception as e:
            return f"Error filling field: {e}"


class BrowserGetElementsTool(BaseTool):
    """List interactive elements on the current page."""

    @property
    def name(self) -> str:
        return "browser_get_elements"

    @property
    def description(self) -> str:
        return (
            "List interactive elements (links, buttons, inputs) on the current page. "
            "Useful for understanding what actions are available before clicking or filling."
        )

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self) -> str:
        try:
            page = await _get_page()
            elements = await page.evaluate("""() => {
                const results = [];
                // Links
                document.querySelectorAll('a[href]').forEach(el => {
                    const text = el.innerText.trim().substring(0, 60);
                    if (text) results.push({type: 'link', text, href: el.href});
                });
                // Buttons
                document.querySelectorAll('button, input[type="submit"]').forEach(el => {
                    const text = (el.innerText || el.value || '').trim().substring(0, 60);
                    if (text) results.push({type: 'button', text});
                });
                // Inputs
                document.querySelectorAll('input:not([type="hidden"]), textarea, select').forEach(el => {
                    results.push({
                        type: 'input',
                        inputType: el.type || 'text',
                        name: el.name || '',
                        placeholder: el.placeholder || '',
                        label: el.labels?.[0]?.innerText?.trim() || '',
                    });
                });
                return results.slice(0, 50);
            }""")
            if not elements:
                return "No interactive elements found on the page."
            return json.dumps(elements, indent=2)
        except Exception as e:
            return f"Error getting elements: {e}"
