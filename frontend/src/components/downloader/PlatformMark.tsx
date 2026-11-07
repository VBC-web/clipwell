import { PLATFORMS, type PlatformKey } from '../../lib/platforms';
import icons from '../../lib/platform-icons.json';

interface Props {
  platform: PlatformKey;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function PlatformMark({ platform, size = 'md', className = '' }: Props) {
  const icon = icons[platform];
  const definition = PLATFORMS[platform];
  const sizeClass =
    size === 'lg' ? 'platform-mark-lg' : size === 'sm' ? '!h-7 !w-7' : '';

  return (
    <span
      className={`platform-mark ${definition.colorClass} ${sizeClass} ${className}`}
      role="img"
      aria-label={`${definition.name} logo`}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d={icon.path} />
      </svg>
    </span>
  );
}
