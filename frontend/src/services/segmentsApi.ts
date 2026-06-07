import type {
  SegmentCustomersResponse,
  SegmentsResponse,
} from "../types/segments";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchSegments(): Promise<SegmentsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/segments`);

  if (!response.ok) {
    throw new Error("Failed to load segments");
  }

  return response.json();
}

export async function fetchSegmentCustomers(
  segmentName: string
): Promise<SegmentCustomersResponse> {
  const encodedSegmentName = encodeURIComponent(segmentName);

  const response = await fetch(
    `${API_BASE_URL}/api/segments/${encodedSegmentName}/customers`
  );

  if (!response.ok) {
    throw new Error("Failed to load segment customers");
  }

  return response.json();
}