/**
 * className 병합 유틸리티
 * falsy 값은 필터링하고 나머지를 공백으로 결합
 * @param  {...(string|boolean|null|undefined)} classes
 * @returns {string}
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}
