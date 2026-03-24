import { Button } from '../../../shared/ui';
import { cn } from '../../../shared/lib/cn';
import { usePlayerListStore } from '../model/usePlayerList';

export function AddPlayerButton({ className }) {
  const addPlayerInput = usePlayerListStore((s) => s.addPlayerInput);
  const playerInputs = usePlayerListStore((s) => s.playerInputs);
  const canAdd = playerInputs.length < 5;

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={addPlayerInput}
      disabled={!canAdd}
      className={cn('w-full border-dashed', className)}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        className="w-4 h-4"
      >
        <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
      </svg>
      <span>소환사 추가</span>
      <span className="text-gray-500 text-xs">
        ({playerInputs.length}/5)
      </span>
    </Button>
  );
}
