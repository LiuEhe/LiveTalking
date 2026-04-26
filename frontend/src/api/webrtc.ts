/** WebRTC 相关 API 请求封装 */

export interface OfferPayload {
  sdp: string
  type: string
}

export interface OfferResponse {
  sdp: string
  type: string
  sessionid: number
  /** 非零时表示后端返回了业务错误 */
  code?: number
  msg?: string
}

/**
 * 向后端提交 WebRTC Offer，获取 Answer。
 * 若后端返回 code !== 0（业务错误，如形象不存在），则抛出包含 msg 的 Error。
 */
export async function postOffer(payload: OfferPayload): Promise<OfferResponse> {
  const res = await fetch('/api/v1/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  }

  const data: OfferResponse = await res.json()

  // 后端通过 Success 路由统一返回 {code: -1, msg: "..."} 表示业务错误
  if (data.code !== undefined && data.code !== 0) {
    throw new Error(data.msg ?? '后端返回未知错误')
  }

  return data
}
