// 간단한 E.164 정규화(한국 번호 중심)
export function normalizePhone(input: string): string {
  const digits = input.replace(/[^0-9+]/g, '')
  if (!digits) return ''

  // 이미 국제 형식
  if (digits.startsWith('+')) {
    return digits
  }

  // 0으로 시작하는 한국 국내 번호를 +82로 변환
  if (digits.startsWith('010')) {
    return '+82' + digits.slice(1)
  }
  if (digits.startsWith('0')) {
    // 기타 국내 지역번호 케이스: 0 제거 후 +82 접두
    return '+82' + digits.slice(1)
  }
  // 그 외는 그대로 두되, 최소 길이 확인은 호출부에서 처리
  return digits
}

export function isValidE164(phone: string): boolean {
  // +[1-15 digits], 대략 검증
  return /^\+[1-9]\d{7,14}$/.test(phone)
}

