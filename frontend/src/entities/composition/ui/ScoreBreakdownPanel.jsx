import { cn } from '../../../shared/lib/cn';

const DIMENSION_LABELS = {
  personal_mastery: '개인 숙련도',
  meta_tier: '메타 티어',
  ad_ap_balance: 'AD/AP 밸런스',
  frontline: '프론트라인',
  deal_composition: '딜 구성',
  waveclear: '웨이브클리어',
  splitpush: '스플릿푸시',
};

const DIMENSION_ORDER = [
  'personal_mastery',
  'meta_tier',
  'ad_ap_balance',
  'frontline',
  'deal_composition',
  'waveclear',
  'splitpush',
];

function getBarColor(score) {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 60) return 'bg-amber-500';
  if (score >= 40) return 'bg-orange-500';
  return 'bg-red-500';
}

export function ScoreBreakdownPanel({ breakdown }) {
  if (!breakdown) return null;

  const dimensions = DIMENSION_ORDER
    .map((key) => ({
      key,
      label: DIMENSION_LABELS[key],
      ...breakdown[key],
    }))
    .filter((d) => d.weight > 0);

  const { penalties } = breakdown;

  return (
    <div className="space-y-2">
      {dimensions.map((dim) => (
        <div key={dim.key} className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400 w-[80px] shrink-0 text-right">
            {dim.label}
          </span>
          <div className="flex-1 flex items-center gap-2">
            <div className="flex-1 h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={cn('h-full rounded-full transition-all', getBarColor(dim.score))}
                style={{ width: `${Math.min(Math.max(dim.score, 0), 100)}%` }}
              />
            </div>
            <span className="text-[10px] text-gray-300 w-[32px] text-right font-medium">
              {dim.score.toFixed(0)}
            </span>
            <span className="text-[10px] text-gray-500 w-[36px] text-right">
              +{dim.weighted.toFixed(1)}
            </span>
          </div>
        </div>
      ))}

      {penalties && penalties.details && penalties.details.length > 0 && (
        <div className="pt-1 border-t border-gray-800">
          {penalties.details.map((detail, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-[10px] text-red-400 w-[80px] shrink-0 text-right">
                {i === 0 ? '페널티' : ''}
              </span>
              <span className="text-[10px] text-red-400 flex-1">
                {detail}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
