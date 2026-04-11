import { getBackendUrl } from "@/lib/api";
import { NextRequest, NextResponse } from "next/server";

/**
 * API Route: /api/kg/supply-chain/[name]
 * 代理到后端 http://localhost:8001/api/kg/supply_chain/{name}
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { name: string } }
) {
  const name = decodeURIComponent(params.name);
  const searchParams = request.nextUrl.searchParams;
  const direction = searchParams.get("direction") || "upstream";
  
  const backendUrl = `${getBackendUrl()}/api/kg/supply_chain/${encodeURIComponent(name)}?direction=${direction}`;

  try {
    const response = await fetch(backendUrl, {
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
