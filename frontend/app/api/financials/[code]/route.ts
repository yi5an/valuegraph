import { getBackendUrl } from "@/lib/api";
import { NextRequest, NextResponse } from "next/server";

/**
 * API Route: /api/financials/[code]
 * 代理到后端 http://localhost:8001/api/financials/{code}
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;
  const searchParams = request.nextUrl.searchParams;
  
  // 构建后端 URL
  const backendUrl = new URL(`${getBackendUrl()}/api/financials/${code}`);
  
  // 转发所有查询参数
  searchParams.forEach((value, key) => {
    backendUrl.searchParams.append(key, value);
  });

  try {
    const response = await fetch(backendUrl.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
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
