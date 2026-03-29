import { NextRequest, NextResponse } from "next/server";

/**
 * API Route: /api/qa/ask
 * 代理到后端 http://localhost:8001/api/qa/ask
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch("http://localhost:8001/api/qa/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
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
    console.error("QA API proxy error:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}
