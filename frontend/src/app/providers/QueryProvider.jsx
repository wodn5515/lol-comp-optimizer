/**
 * 글로벌 프로바이더
 * zustand를 사용하므로 별도의 Query Provider는 필요 없으나,
 * 향후 확장을 위한 프로바이더 래퍼
 */
export function AppProvider({ children }) {
  return <>{children}</>;
}
