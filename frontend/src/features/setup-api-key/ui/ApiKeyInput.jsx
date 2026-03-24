import { useState } from 'react';
import { Input, Button } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { useApiKeyStore } from '../model/useApiKey';

export function ApiKeyInput({ className }) {
  const { apiKey, isValid, setApiKey } = useApiKeyStore();
  const [visible, setVisible] = useState(false);
  const [localKey, setLocalKey] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setApiKey(localKey.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSave();
  };

  const maskedValue = visible
    ? localKey
    : localKey
      ? localKey.slice(0, 8) + '*'.repeat(Math.max(0, localKey.length - 8))
      : '';

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-300">
          Riot API 키
        </label>
        <a
          href="https://developer.riotgames.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          API 키 발급 안내 &rarr;
        </a>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type={visible ? 'text' : 'password'}
            value={localKey}
            onChange={(e) => {
              setLocalKey(e.target.value);
              setSaved(false);
            }}
            onKeyDown={handleKeyDown}
            placeholder="RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            className={cn(
              'w-full rounded-lg border bg-slate-900/80 px-4 py-2.5 text-sm text-gray-100 pr-10',
              'placeholder:text-gray-600',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-gray-950',
              isValid
                ? 'border-emerald-600/40 focus:ring-emerald-500/40'
                : localKey
                  ? 'border-amber-600/40 focus:ring-amber-500/40'
                  : 'border-slate-600/50 focus:ring-amber-500/40'
            )}
          />
          <button
            type="button"
            onClick={() => setVisible(!visible)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors text-sm"
            tabIndex={-1}
          >
            {visible ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.745-1.745a10.029 10.029 0 003.3-4.38 1.651 1.651 0 000-1.185A10.004 10.004 0 009.999 3a9.956 9.956 0 00-4.744 1.194L3.28 2.22zM7.752 6.69l1.092 1.092a2.5 2.5 0 013.374 3.373l1.092 1.092a4 4 0 00-5.558-5.558z" clipRule="evenodd" />
                <path d="M10.748 13.93l2.523 2.523A9.987 9.987 0 0110 17c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 012.838-4.308l2.468 2.469a4 4 0 005.555 5.554l.43.214z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
                <path fillRule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        </div>

        <Button
          variant={saved ? 'secondary' : 'primary'}
          size="md"
          onClick={handleSave}
          disabled={!localKey.trim()}
        >
          {saved ? '\u2713 저장됨' : '저장'}
        </Button>
      </div>

      {localKey && !isValid && (
        <p className="text-[11px] text-amber-400/80">
          API 키는 &quot;RGAPI-&quot;로 시작해야 합니다. Dev 키는 24시간마다 갱신이 필요합니다.
        </p>
      )}
      {isValid && (
        <p className="text-[11px] text-emerald-400/80">
          API 키가 설정되었습니다. 키는 브라우저에만 저장됩니다.
        </p>
      )}
    </div>
  );
}
