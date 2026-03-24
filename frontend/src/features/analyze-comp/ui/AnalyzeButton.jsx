import { Button } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';

export function AnalyzeButton({
  onClick,
  disabled = false,
  loading = false,
  className,
}) {
  return (
    <Button
      variant="primary"
      size="lg"
      onClick={onClick}
      disabled={disabled}
      loading={loading}
      className={cn('w-full text-base font-bold tracking-wide', className)}
    >
      {loading ? '분석 중...' : '조합 분석하기'}
    </Button>
  );
}
