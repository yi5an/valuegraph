import { getBackendUrl } from "@/lib/api";
import { NextRequest, NextResponse } from "next/server";

/**
 * API Route: /api/stats/daily-report
 * 代理到后端
 */
export async function GET() {
  try {
    const response = await fetch(`${getBackendUrl()}/api/stats/daily-report`, {
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
    console.error("Stats API proxy error:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}
