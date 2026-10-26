"""Deployment & Connection Diagnostic Script.

Tests Render backend, PostgreSQL database, and Vercel frontend proxying.

Usage:
    python check_connections.py
    python check_connections.py https://your-project.vercel.app
"""

import sys
import json
import time
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RENDER_BACKEND_URL = "https://srpbackend.onrender.com"


def check_url(url, method="GET", headers=None):
    headers = headers or {}
    start = time.time()
    try:
        req = urllib.request.Request(url, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as res:
            elapsed = round((time.time() - start) * 1000)
            body = res.read().decode("utf-8")
            return {
                "ok": True,
                "status_code": res.status,
                "elapsed_ms": elapsed,
                "body": body,
                "headers": dict(res.headers),
            }
    except urllib.error.HTTPError as e:
        elapsed = round((time.time() - start) * 1000)
        body = e.read().decode("utf-8") if e.fp else ""
        return {
            "ok": False,
            "status_code": e.code,
            "elapsed_ms": elapsed,
            "body": body,
            "headers": dict(e.headers),
            "error": str(e),
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        return {
            "ok": False,
            "status_code": None,
            "elapsed_ms": elapsed,
            "error": str(e),
        }


def run_diagnostics(vercel_url=None):
    print("=" * 70)
    print(" 🔍 STUDENT RESULT PORTAL - DEPLOYMENT & CONNECTION CHECKER")
    print("=" * 70)

    # 1. Direct Render Backend Health Check
    print("\n[1/4] Checking Render Backend Service...")
    health_url = f"{RENDER_BACKEND_URL}/api/v1/health"
    print(f"      Target: {health_url}")
    res = check_url(health_url)

    if res["ok"]:
        try:
            data = json.loads(res["body"])
            db_status = data.get("database", "unknown")
            service = data.get("service", "unknown")
            env = data.get("environment", "unknown")
            print(f"      ✅ Backend Online ({res['elapsed_ms']}ms)")
            print(f"      • Service:     {service}")
            print(f"      • Environment: {env}")
            print(f"      • Database:    {db_status}")
            if db_status != "connected":
                print(f"      ⚠️  Warning: Database is '{db_status}'!")
        except Exception:
            print(f"      ✅ Reachable (Status {res['status_code']})")
    else:
        print(f"      ❌ Failed: {res.get('error', 'Unreachable')}")
        if res.get("elapsed_ms", 0) > 10000:
            print("      ⏳ Note: Render free-tier container may be cold and waking up (~50s).")

    # 2. Check Auth / Setup Status
    print("\n[2/4] Checking Auth & Initialization Status...")
    setup_url = f"{RENDER_BACKEND_URL}/api/v1/auth/setup-status"
    res_setup = check_url(setup_url)
    if res_setup["ok"]:
        try:
            data = json.loads(res_setup["body"])
            needs_setup = data.get("needs_setup", False)
            if needs_setup:
                print("      ℹ️  System Setup Status: Clean database (needs initial admin).")
            else:
                print("      ✅ System Setup Status: Admin account initialized.")
        except Exception:
            print(f"      ✅ Status {res_setup['status_code']}")
    else:
        print(f"      ⚠️  Auth probe returned: {res_setup.get('error')}")

    # 3. Check CORS Support for Vercel
    print("\n[3/4] Checking CORS Preflight Permissions...")
    test_origin = vercel_url or "https://student-result-portal.vercel.app"
    cors_res = check_url(
        f"{RENDER_BACKEND_URL}/api/v1/auth/login",
        method="OPTIONS",
        headers={
            "Origin": test_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    if cors_res["ok"]:
        allow_origin = cors_res.get("headers", {}).get("access-control-allow-origin")
        print(f"      ✅ CORS Preflight Allowed for origin: {test_origin}")
        print(f"      • Access-Control-Allow-Origin: {allow_origin}")
    else:
        print(f"      ⚠️  CORS test returned status {cors_res.get('status_code')}")

    # 4. Check Vercel Frontend & Rewrites (if URL provided)
    if vercel_url:
        print(f"\n[4/4] Checking Vercel Frontend: {vercel_url}...")
        res_v = check_url(vercel_url)
        if res_v["ok"]:
            print(f"      ✅ Frontend Home is accessible ({res_v['elapsed_ms']}ms)")
        else:
            print(f"      ❌ Frontend Home failed: {res_v.get('error')}")

        proxy_url = f"{vercel_url.rstrip('/')}/api/v1/health"
        print(f"      Testing Vercel API Proxy: {proxy_url}...")
        res_proxy = check_url(proxy_url)
        if res_proxy["ok"]:
            print(f"      ✅ Vercel /api rewrite proxy is WORKING! ({res_proxy['elapsed_ms']}ms)")
            print(f"      • Response: {res_proxy['body'].strip()}")
        else:
            print(f"      ❌ Vercel /api rewrite proxy FAILED! (Status: {res_proxy.get('status_code')})")
            print("      💡 Action Required in Vercel:")
            print("         1. Verify that 'vercel.json' is deployed with the rewrite rules.")
            print("         2. In Vercel Project Settings -> General -> Root Directory:")
            print("            Set Root Directory to 'frontend', OR keep root vercel.json.")
            print("         3. Alternatively, set Environment Variable in Vercel:")
            print("            VITE_API_BASE_URL=https://srpbackend.onrender.com/api/v1")
    else:
        print("\n[4/4] Vercel Frontend Check:")
        print("      To test your specific Vercel deployment, run:")
        print("      python check_connections.py https://<your-project>.vercel.app")

    print("\n" + "=" * 70)
    print(" 🏁 DIAGNOSTICS COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    v_url = sys.argv[1] if len(sys.argv) > 1 else None
    run_diagnostics(v_url)
