export function toDateInputValue(d = new Date()) {
  return d.toISOString().slice(0, 10);
}

export function formatRelativeDateTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const isSameDay = now.toDateString() === date.toDateString();
  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  const isYesterday = yesterday.toDateString() === date.toDateString();
  
  const timeString = date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
  
  if (isSameDay) return `Today at ${timeString}`;
  if (isYesterday) return `Yesterday at ${timeString}`;
  
  const includeYear = date.getFullYear() !== now.getFullYear();
  const formattedDate = date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(includeYear ? { year: 'numeric' } : {}),
  });
  
  return `${formattedDate} at ${timeString}`;
}
