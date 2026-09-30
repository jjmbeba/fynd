export async function http<T>(url: string, options: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  const body = [204, 205, 304].includes(response.status) ? null : await response.text()

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const data: unknown = body ? JSON.parse(body) : {}
  return { data, status: response.status, headers: response.headers } as T
}
