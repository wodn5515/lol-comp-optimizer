import { useState } from 'react';
import { CHAMPION_ICON_URL } from '../../../shared/config/constants';
import { cn } from '../../../shared/lib/cn';

export function ChampionIcon({
  championName,
  championId,
  size = 32,
  className,
  showTooltip = true,
}) {
  const [error, setError] = useState(false);
  const [showName, setShowName] = useState(false);

  const imgSrc = error
    ? CHAMPION_ICON_URL('Aatrox')
    : CHAMPION_ICON_URL(championName);

  return (
    <div
      className={cn('relative inline-block', className)}
      onMouseEnter={() => showTooltip && setShowName(true)}
      onMouseLeave={() => setShowName(false)}
    >
      <img
        src={imgSrc}
        alt={championName || `Champion ${championId}`}
        width={size}
        height={size}
        className="rounded-md object-cover"
        style={{ width: size, height: size }}
        onError={() => setError(true)}
      />
      {showName && showTooltip && championName && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-800 border border-slate-600/50 rounded text-[10px] text-gray-200 whitespace-nowrap z-50 shadow-lg">
          {championName}
        </div>
      )}
    </div>
  );
}
