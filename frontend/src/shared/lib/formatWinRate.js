/**
 * 승률을 퍼센트 문자열로 포맷팅
 * @param {number} rate - 0~1 사이 승률
 * @param {number} decimals - 소수점 자릿수 (기본 1)
 * @returns {string} 포맷된 승률 문자열 (예: "67.5%")
 */
export function formatWinRate(rate, decimals = 1) {
  if (rate == null || isNaN(rate)) return '-';
  return `${(rate * 100).toFixed(decimals)}%`;
}
