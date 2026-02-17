#!/usr/bin/env python3
"""Automate Xiaoheihe daily check-in with browser login fallback."""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

WORKSPACE = Path("/root/.openclaw/workspace")
COOKIE_FILE = WORKSPACE / "secrets/xiaoheihe_cookies.json"
SCREENSHOT_DIR = WORKSPACE / "screenshots"
HOME_URL = "https://www.xiaoheihe.cn/app/bbs/home"

LOGIN_PROMPT_KEYWORDS = ("验证码登录", "密码登录")
CHECKIN_BUTTON_TEXTS = (
    "立即签到",
    "今日签到",
    "去签到",
    "签到",
    "签到打卡",
    "打卡",
)
CHECKIN_ENTRY_TEXTS = (
    "任务中心",
    "每日任务",
    "成长任务",
    "任务",
)
ALREADY_DONE_KEYWORDS = (
    "今日已签到",
    "已签到",
    "连续签到",
)
SUCCESS_KEYWORDS = (
    "签到成功",
    "打卡成功",
    "领取成功",
)


def now_cn() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def load_cookies() -> list[dict]:
    if not COOKIE_FILE.exists():
        return []
    try:
        data = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
        cookies = data.get("cookies", [])
        return cookies if isinstance(cookies, list) else []
    except Exception:
        return []


async def save_cookies(context) -> None:
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "cookies": await context.cookies(),
    }
    COOKIE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def get_page_text(page) -> str:
    try:
        text = await page.inner_text("body")
        return text.strip()
    except Exception:
        return ""


async def get_store_login_state(page) -> bool | None:
    """Read login state from Nuxt store when available."""
    try:
        value = await page.evaluate(
            """() => {
                try {
                    const app = window.useNuxtApp?.();
                    const state = app?.$pinia?.state?.value?.UserStore?.is_logined;
                    return typeof state === 'boolean' ? state : null;
                } catch (e) {
                    return null;
                }
            }"""
        )
        if isinstance(value, bool):
            return value
    except Exception:
        pass
    return None


async def has_top_login_button(page) -> bool:
    """Detect the top-right login button (logged-out indicator)."""
    locator = page.locator("button:has-text('登录')")
    try:
        count = await locator.count()
    except Exception:
        return False

    for index in range(min(count, 5)):
        item = locator.nth(index)
        try:
            if not await item.is_visible():
                continue
            box = await item.bounding_box()
            if box and box.get("y", 9999) < 180:
                return True
        except Exception:
            continue
    return False


async def is_logged_in(page) -> bool:
    store_state = await get_store_login_state(page)
    if store_state is not None:
        return store_state

    text = await get_page_text(page)
    if not text:
        return False

    if all(keyword in text for keyword in LOGIN_PROMPT_KEYWORDS):
        return False
    if "扫码快捷登录" in text:
        return False
    if await has_top_login_button(page):
        return False
    return True


async def click_first_visible_text(page, text_candidates: tuple[str, ...]) -> str | None:
    for candidate in text_candidates:
        locator = page.get_by_text(candidate, exact=False)
        try:
            count = await locator.count()
        except Exception:
            continue

        for index in range(min(count, 5)):
            item = locator.nth(index)
            try:
                if not await item.is_visible():
                    continue
                await item.click(timeout=2000)
                await page.wait_for_timeout(1200)
                return candidate
            except Exception:
                continue
    return None


async def open_login_modal(page) -> bool:
    clicked = await click_first_visible_text(page, ("登录", "注册/登录"))
    if not clicked:
        return False

    for _ in range(10):
        text = await get_page_text(page)
        if "扫码快捷登录" in text:
            return True
        await page.wait_for_timeout(500)
    return False


async def wait_for_login(page, timeout_seconds: int) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    while asyncio.get_event_loop().time() < deadline:
        if await is_logged_in(page):
            return True
        await page.wait_for_timeout(2000)
    return False


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


async def attempt_checkin(page) -> tuple[bool, str]:
    # Strategy 1: home page direct check-in
    clicked = await click_first_visible_text(page, CHECKIN_BUTTON_TEXTS)
    if clicked:
        text = await get_page_text(page)
        if contains_any(text, SUCCESS_KEYWORDS) or contains_any(text, ALREADY_DONE_KEYWORDS):
            return True, f"home:{clicked}"

    # Strategy 2: go to profile and task center
    await click_first_visible_text(page, ("我", "个人中心", "我的"))
    await page.wait_for_timeout(1500)

    entry_clicked = await click_first_visible_text(page, CHECKIN_ENTRY_TEXTS)
    if entry_clicked:
        await page.wait_for_timeout(1500)

    clicked = await click_first_visible_text(page, CHECKIN_BUTTON_TEXTS)
    if clicked:
        text = await get_page_text(page)
        if contains_any(text, SUCCESS_KEYWORDS) or contains_any(text, ALREADY_DONE_KEYWORDS):
            return True, f"profile:{clicked}"

    # Strategy 3: candidate paths
    for path in (
        "https://www.xiaoheihe.cn/app/user/task",
        "https://www.xiaoheihe.cn/app/user/tasks",
        "https://www.xiaoheihe.cn/app/user/profile",
    ):
        try:
            await page.goto(path, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1800)
        except PlaywrightTimeoutError:
            continue

        text = await get_page_text(page)
        if contains_any(text, ALREADY_DONE_KEYWORDS):
            return True, f"path:{path}"

        clicked = await click_first_visible_text(page, CHECKIN_BUTTON_TEXTS)
        if clicked:
            text = await get_page_text(page)
            if contains_any(text, SUCCESS_KEYWORDS) or contains_any(text, ALREADY_DONE_KEYWORDS):
                return True, f"path:{path}:{clicked}"

    return False, "no-entry"


async def run(headless: bool, allow_qr_login: bool, login_wait_seconds: int) -> tuple[bool, str]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_file = SCREENSHOT_DIR / "xiaoheihe_checkin_latest.png"
    qr_file = SCREENSHOT_DIR / "xiaoheihe_qrcode.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 900})

        cookies = load_cookies()
        if cookies:
            await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2500)

        logged_in = await is_logged_in(page)

        if not logged_in and allow_qr_login:
            opened = await open_login_modal(page)
            if not opened:
                await page.screenshot(path=str(screenshot_file), full_page=True)
                await browser.close()
                return (
                    False,
                    f"⚠️ 小黑盒未能打开登录弹窗（截图：{screenshot_file}，时间：{now_cn()}）。",
                )

            await page.screenshot(path=str(qr_file), full_page=True)
            logged_in = await wait_for_login(page, login_wait_seconds)
            if logged_in:
                await page.wait_for_timeout(1200)

            if not logged_in:
                await page.screenshot(path=str(screenshot_file), full_page=True)
                await browser.close()
                return (
                    False,
                    f"⚠️ 小黑盒登录超时，未完成扫码（截图：{qr_file}，时间：{now_cn()}）。",
                )

        if not logged_in:
            await page.screenshot(path=str(screenshot_file), full_page=True)
            await browser.close()
            return (
                False,
                f"⚠️ 小黑盒未登录，无法自动签到（截图：{screenshot_file}，时间：{now_cn()}）。",
            )

        ok, route = await attempt_checkin(page)
        text = await get_page_text(page)
        already_done = contains_any(text, ALREADY_DONE_KEYWORDS)
        await save_cookies(context)
        await page.screenshot(path=str(screenshot_file), full_page=True)
        await browser.close()

        if ok:
            if already_done:
                return True, f"ℹ️ 小黑盒今日已签到（{now_cn()}，路径：{route}）。"
            return True, f"✅ 小黑盒签到完成（{now_cn()}，路径：{route}）。"

        return (
            False,
            f"⚠️ 小黑盒签到失败：未找到可点击的签到入口（截图：{screenshot_file}，时间：{now_cn()}）。",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Xiaoheihe daily check-in")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument(
        "--allow-qr-login",
        action="store_true",
        help="Open login flow and wait for QR scan when cookies are invalid",
    )
    parser.add_argument(
        "--login-wait-seconds",
        type=int,
        default=120,
        help="How long to wait for QR login",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    success, message = asyncio.run(
        run(
            headless=args.headless,
            allow_qr_login=args.allow_qr_login,
            login_wait_seconds=args.login_wait_seconds,
        )
    )
    print(message)
    raise SystemExit(0 if success else 1)
