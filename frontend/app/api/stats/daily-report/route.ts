import { NextResponse } from "next/server";

/**
 * API Route: /api/stats/daily-report
 * 代理到后端 http://localhost:8001/api/stats/daily-report
 */
export async function GET() {
  try {
    const response = await fetch("http://localhost:8001/api/stats/daily-report", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: "Failed to fetch from backend" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API proxy error:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}
