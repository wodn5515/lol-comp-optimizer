import { PieChartWidget, BarChartWidget } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';

export function TeamAnalysisChart({ teamAnalysis }) {
  const {
    ad_ratio,
    ap_ratio,
    has_frontline,
    waveclear_score,
    splitpush_score,
    teamfight_score,
    engage_score,
    peel_score,
    poke_score,
    pick_score,
    burst_score,
    comp_type,
    strategy_guide,
    strengths,
    weaknesses,
  } = teamAnalysis;

  const damageData = [
    { name: 'AD', value: Math.round((ad_ratio || 0) * 100), color: '#e44040' },
    { name: 'AP', value: Math.round((ap_ratio || 0) * 100), color: '#576bce' },
  ];

  const statsData = [
    { name: '팀파', value: teamfight_score || 0 },
    { name: '이니시', value: engage_score || 0 },
    { name: '포킹', value: poke_score || 0 },
    { name: '캐치', value: pick_score || 0 },
    { name: '폭딜', value: burst_score || 0 },
    { name: '클리어', value: waveclear_score || 0 },
    { name: '스플릿', value: splitpush_score || 0 },
    { name: '필링', value: peel_score || 0 },
  ];

  return (
    <div className="border-t border-gray-800 pt-4">
      {comp_type && (
        <div className="mb-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-950 border border-amber-800">
            <span className="text-xs font-bold text-amber-400">{comp_type}</span>
          </div>
        </div>
      )}

      <h4 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
        팀 분석
      </h4>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-[10px] text-gray-500 mb-1 text-center">딜 타입 비율</p>
          <PieChartWidget
            data={damageData}
            height={140}
            innerRadius={30}
            outerRadius={50}
          />
        </div>
        <div>
          <p className="text-[10px] text-gray-500 mb-1 text-center">팀 능력치</p>
          <BarChartWidget
            data={statsData}
            height={180}
            barColor="#0397ab"
            layout="vertical"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <div
          className={cn(
            'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full',
            has_frontline
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              : 'bg-red-950 text-red-400 border border-red-800'
          )}
        >
          <span>{has_frontline ? '\u2713' : '\u2717'}</span>
          <span>프론트라인</span>
        </div>
      </div>

      {strengths && strengths.length > 0 && (
        <div className="mb-2">
          <p className="text-[10px] font-medium text-emerald-400 mb-1">강점</p>
          <div className="flex flex-wrap gap-1">
            {strengths.map((s, i) => (
              <span
                key={i}
                className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {weaknesses && weaknesses.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-medium text-red-400 mb-1">약점</p>
          <div className="flex flex-wrap gap-1">
            {weaknesses.map((w, i) => (
              <span
                key={i}
                className="text-[10px] px-2 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-800"
              >
                {w}
              </span>
            ))}
          </div>
        </div>
      )}

      {strategy_guide && (
        <div className="mt-3 p-3 rounded-lg bg-sky-950 border border-sky-800">
          <p className="text-[10px] font-semibold text-sky-400 mb-1.5">
            운영 가이드
          </p>
          {strategy_guide.split('\n').map((line, i) => (
            <p key={i} className="text-[11px] text-gray-300 leading-relaxed">
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
